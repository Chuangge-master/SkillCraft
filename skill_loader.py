from agents import function_tool
from typing import Callable, List, Optional, Dict, Any, Type
from pathlib import Path
from pydantic import BaseModel, create_model
import yaml
from agents import FunctionTool
import json
import importlib.util
import inspect

class Skill:
    name:str = '',
    description:str = '',
    tool:Optional[FunctionTool] = None
    run_by_script: bool = False
    when_to_use:str = ''



class SkillLoader:
    def __init__(self, skill_dir:str):
        self.skill_dir = Path(skill_dir)
        self.skills:List[Skill] = []
        self._skill_cache: Dict[str, Dict[str, Any]] = {}  # 缓存技能信息，key为技能目录名，value包含技能对象和文件修改时间
    
    def clear_cache(self):
        """清空缓存，下次加载将重新加载所有技能"""
        self._skill_cache.clear()
        self.skills.clear()

    def load_skills(self, force_reload: bool = False):
        """
        加载技能，支持缓存机制
        
        Args:
            force_reload: 是否强制重新加载所有技能，忽略缓存
        """
        self.skills.clear()
        updated_skills = []
        
        for item in self.skill_dir.rglob("*"):
            if not item.is_dir():
                continue

            skill_name = item.name
            md_path = item / "SKILL.md"
            run_path = item / "skill.py"

            if not md_path.exists():
                # 如果技能目录存在但没有SKILL.md，移除缓存
                if skill_name in self._skill_cache:
                    del self._skill_cache[skill_name]
                continue
            
            # 获取文件修改时间
            md_mtime = md_path.stat().st_mtime
            run_mtime = run_path.stat().st_mtime if run_path.exists() else 0
            current_mtime = max(md_mtime, run_mtime)
            
            # 检查缓存是否存在且有效
            if not force_reload and skill_name in self._skill_cache:
                cached_info = self._skill_cache[skill_name]
                if cached_info['mtime'] >= current_mtime:
                    # 使用缓存的技能
                    self.skills.append(cached_info['skill'])
                    continue
            
            # 缓存无效或不存在，重新加载技能
            meta_dict = self.parse_skill_md(md_path)
            if not meta_dict or 'name' not in meta_dict:
                print(f"⚠️ SKILL.md in {item} missing 'name' field")
                if skill_name in self._skill_cache:
                    del self._skill_cache[skill_name]
                continue

            name = meta_dict['name']
            description = meta_dict.get('description', '')
            when_to_use = meta_dict.get('when_to_use', '')
            run_by_script = meta_dict.get('run_by_script', False)

            skill = Skill()
            desc = description.replace("\n", " ").strip()
            skill.name = name
            skill.description = desc
            skill.run_by_script = run_by_script
            skill.when_to_use = when_to_use
            
            if run_path.exists():
                run_function = self.get_run_function(run_path)
                run_function_args = self.get_run_function_args(run_path)
                
                tool = FunctionTool(
                    name=name,
                    description=f"{description}\nwhen to use: {when_to_use}",
                    params_json_schema=run_function_args.model_json_schema(),
                    on_invoke_tool=run_function,
                )
                skill.tool = tool
            
            # 更新缓存
            self._skill_cache[skill_name] = {
                'skill': skill,
                'mtime': current_mtime
            }
            
            self.skills.append(skill)
            updated_skills.append(skill_name)
        
        # 检查是否有技能被删除
        existing_skills = {item.name for item in self.skill_dir.rglob("*") if item.is_dir() and (item / "SKILL.md").exists()}
        for cached_skill_name in list(self._skill_cache.keys()):
            if cached_skill_name not in existing_skills:
                del self._skill_cache[cached_skill_name]
        
        if updated_skills:
            print(f"🔄 已更新技能: {', '.join(updated_skills)}")
        else:
            print("✅ 所有技能已缓存，无需更新")           

    def parse_skill_md(self, md_path: Path) -> Optional[Dict[str, Any]]:
        content = md_path.read_text(encoding='utf-8')
        if not content.strip().startswith('---'):
            return None
        try:
            parts = content.split('---', 2)
            if len(parts) < 3:
                return None
            yaml_str = parts[1].strip()
            meta = yaml.safe_load(yaml_str)
            if not isinstance(meta, dict):
                return None

            return meta
        except Exception as e:
            print(f"⚠️ Failed to parse {md_path}: {e}")
            return None
        
    def get_run_function(self, run_path: Path) -> Callable:
        if not run_path.exists():
            raise FileNotFoundError(f"skill.py 文件不存在: {run_path}")

        spec = importlib.util.spec_from_file_location('run', run_path)
    
        if spec is None or spec.loader is None:
            raise ImportError(f"无法为 {run_path} 创建模块加载器")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 2. 获取 'run' 对象
        if not hasattr(module, 'run'):
            raise AttributeError(f"在文件 {run_path} 中未找到 'run' 对象")
        
        run_func = module.run

        # 3. 检查是否为函数
        if not inspect.isfunction(run_func):
            raise TypeError(f"'run' 不是一个函数 (当前类型: {type(run_func).__name__})")

        # 4. 检查是否为协程函数
        if not inspect.iscoroutinefunction(run_func):
            raise TypeError(f"'run' 不是一个 async 函数")

        return run_func
        
    def get_run_function_args(self, run_path: Path) -> BaseModel:
        # 1. 动态加载模块
        spec = importlib.util.spec_from_file_location('FunctionArgs', run_path)
        
        if spec is None or spec.loader is None:
            raise ImportError(f"无法为 {run_path} 创建模块加载器")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 2. 从模块中获取类
        if not hasattr(module, 'FunctionArgs'):
            raise AttributeError(f"在文件 {run_path} 中未找到类 '{'FunctionArgs'}'")
        
        loaded_class = getattr(module, 'FunctionArgs')

        # 3. 验证它是否继承自 BaseModel
        # inspect.getmro 获取类的继承链
        if not issubclass(loaded_class, BaseModel):
            raise TypeError(f"类 '{'FunctionArgs'}' 必须继承自 pydantic.BaseModel")

        return loaded_class # type: ignore
    
if __name__ == '__main__':
    loader = SkillLoader("skills")
    loader.load_skills()
    for tool in loader.skills:
        if isinstance(tool, FunctionTool):
            print('name: ', tool.name)
            print('description: ',tool.description)
            print(json.dumps(tool.params_json_schema, indent=2))
            print()
