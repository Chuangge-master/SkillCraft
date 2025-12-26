from agents import Agent,Runner,RunResult,OpenAIChatCompletionsModel,set_tracing_disabled
from openai import AsyncOpenAI
from skill_loader import SkillLoader

def create_agent(skill_dir: str, 
                 base_url:str,
                 llm_name: str,
                 api_key: str,
                 agent_name: str,
                 agent_description: str,
                 force_reload: bool = False) -> Agent:
    skill_loader = SkillLoader(skill_dir)
    skill_loader.load_skills(force_reload=force_reload)
    agent_description += "\n\n# Additional Capabilities (Not Yet Executable):\n"

    openai_client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    # 存储不用脚本执行，agent直接运行的技能
    skills_direct_run = []

    # 对于没有运行脚本skill.py的技能，需要特殊处理
    for skill in skill_loader.skills:
        if skill.tool is None and skill.run_by_script: # 未实现的脚本技能
            agent_description += f"- {skill.name}: {skill.description}\n"    
        elif skill.tool is None and not skill.run_by_script: # 直接llm运行的技能
            skill_agent = Agent( 
                name=f"{skill.name} Assistant",
                instructions=f"you are a assistant with skill {skill.name}, you can {skill.description}",
                model=OpenAIChatCompletionsModel(
                    model=llm_name,
                    openai_client=openai_client,
                ),
            )
            skills_direct_run.append(skill_agent.as_tool(
                tool_name=f"{skill.name}",
                tool_description=f"{skill.description}",
            ))

    agent = Agent( 
        name=agent_name,
        instructions=agent_description,
        model=OpenAIChatCompletionsModel(
            model=llm_name,
            openai_client=openai_client,
        ),
        tools=[skill.tool for skill in skill_loader.skills if skill.tool is not None], 
    )
    agent.tools.extend(skills_direct_run)

    return agent

def run_agent(agent: Agent, prompt: str) -> RunResult:
    set_tracing_disabled(True) # 关闭日志
    result = Runner.run_sync(agent, prompt)
    return result

if __name__ == "__main__":
    pass
    
        