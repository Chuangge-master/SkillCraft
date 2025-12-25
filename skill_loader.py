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
    info:str = ''
    tool:Optional[FunctionTool] = None



class SkillLoader:
    def __init__(self, skill_dir:str):
        self.skill_dir = Path(skill_dir)
        self.skills:List[Skill] = []

    def load_skills(self):
        for item in self.skill_dir.rglob("*"):
            if not item.is_dir():
                continue

            skill_name = item.name
            md_path = item / "SKILL.md"
            run_path = item / "skill.py"

            if not md_path.exists():
                continue  # 必须有 SKILL.md

            meta_dict = self.parse_skill_md(md_path)
            # print(json.dumps(meta_dict, indent=2, ensure_ascii=False))

            if not meta_dict or 'name' not in meta_dict:
                print(f"⚠️ SKILL.md in {item} missing 'name' field")
                continue

            name = meta_dict['name']
            description = meta_dict.get('description', '')
            when_to_use = meta_dict.get('when_to_use', '')
            skill = Skill()
            desc = description.replace("\n", " ").strip()
            skill.info += f"- {name}: {desc}\n"
            
            if run_path.exists():
                run_function = self.get_run_function(run_path)
                run_function_args = self.get_run_function_args(run_path)
                # print(json.dumps(run_function_args.model_json_schema(), indent=4, ensure_ascii=False))

                tool = FunctionTool(
                    name=name,
                    description=f"{description}\nwhen to use: {when_to_use}",
                    params_json_schema=run_function_args.model_json_schema(),
                    on_invoke_tool=run_function,
                )
                skill.tool = tool
                
            self.skills.append(skill)           

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
