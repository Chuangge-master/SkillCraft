from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import yaml
from pathlib import Path
from typing import List
import re
import json
import os
import inspect
from pydantic import BaseModel
from typing import Callable
import importlib
from prompts import skill_choose_prompt, run_agent_prompt

class Skill(BaseModel):
    name: str
    description: str
    when_to_use: str
    tools: List[str]

def load_skill(skill_dir: str) -> List[Skill]:
    skill_path = Path(skill_dir)
    skills:List[Skill] = []
    for skill_file in skill_path.rglob("SKILL.md"):  # rglob 递归查找
        try:
            content = skill_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"无法读取文件 {skill_file}: {e}")
            continue

        # 使用正则匹配两个 --- 之间的内容（非贪婪）
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            print(f"文件 {skill_file} 中未找到有效的 YAML front matter")
            continue

        yaml_str = match.group(1)
        try:
            data = yaml.safe_load(yaml_str)
            if data is None:
                data = {}
            
            skill = Skill(
                name = data.get('name', skill_file.parent.name),
                description = data.get('description', ''),
                when_to_use = data.get('when_to_use', ''),
                tools = data.get('tools', []),
            )
            skills.append(skill)
        except yaml.YAMLError as e:
            print(f"YAML 解析失败（{skill_file}）: {e}")
            continue
    
    return skills

def load_skill_tools(skill_dir: str, skill:Skill) -> List[Callable]:
    tool_path = Path(skill_dir) / skill.name / "tools.py"
    if not tool_path.exists():
        print(f"工具文件 {tool_path} 不存在")
        return []
    
    # 动态加载函数，仅加载skill中指定的tools
    spec = importlib.util.spec_from_file_location("tools", tool_path)
    tools_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools_module)
    tools = []
    for name, obj in inspect.getmembers(tools_module, inspect.isfunction):
        if name in skill.tools:
            t = tool(obj)
            tools.append(t)
        
    return tools
    

def chat(user_input:str,
    skill_dir:str,
    base_url:str,
    llm_name:str,
    api_key:str,     
    ):
    llm = ChatOpenAI(
        base_url=base_url,
        model_name=llm_name,
        api_key=api_key,
        temperature=0.7,
    )
    # 技能选择助手
    skills = load_skill(skill_dir)  
    skill_choose_agent_prompt = skill_choose_prompt.replace('#skills#', "\n".join([f"{skill.name}: {skill.description}" for skill in skills]))
    skill_choose_agent = create_agent(
        llm,
        system_prompt=skill_choose_agent_prompt,
    )
    response =  skill_choose_agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    print('skill_choose:',response["messages"][-1].content)

    available_skills = [skill for skill in skills if skill.name in json.loads(response["messages"][-1].content)]
    available_skill_tools = []
    for skill in available_skills:
        available_skill_tools.extend(load_skill_tools(skill_dir=skill_dir,skill=skill))

    # 技能执行助手
    run_agent = create_agent(
        llm,
        system_prompt=run_agent_prompt,
        tools=available_skill_tools,
    )
    # response =  run_agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    # print('run_agent:',response["messages"][-1].content)
    # 流式输出
    response = run_agent.stream({"messages": [{"role": "user", "content": user_input}]}, stream_mode="messages")
    for chunk in response:
        token = chunk[0].content
        print(token, end='', flush=True)

    # TODO 多轮对话实现，其中涉及短期记忆和长期记忆
        
if __name__ == "__main__":
    skills = load_skill(skill_dir='skills')
    print(skills)
    available_skill_tools = load_skill_tools(skill_dir='skills', skill=skills[0])
    print(f"技能 {skills[0].name} 可用的工具：",[tool.name for tool in available_skill_tools])
