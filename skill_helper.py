from agents import Agent,Runner,RunResult,OpenAIChatCompletionsModel,set_tracing_disabled
from openai import AsyncOpenAI
from skill_loader import SkillLoader
import os

def create_agent(skill_dir: str, 
                 base_url:str,
                 llm_name: str,
                 api_key: str,
                 agent_name: str,
                 agent_description: str,) -> Agent:
    skill_loader = SkillLoader(skill_dir)
    skill_loader.load_skills()
    agent_description += "\n\n# Additional Capabilities (Not Yet Executable):\n"
    for skill in skill_loader.skills:
        if skill.tool is None:
            agent_description += f"- {skill.info}\n"    

    openai_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    agent = Agent( 
        name=agent_name,
        instructions=agent_description,
        model=OpenAIChatCompletionsModel(
            model=llm_name,
            openai_client=openai_client,
        ),
        tools=[skill.tool for skill in skill_loader.skills if skill.tool is not None], 
        
    )
    return agent

def run_agent(agent: Agent, prompt: str) -> RunResult:
    result = Runner.run_sync(agent, prompt)
    return result

if __name__ == "__main__":
    set_tracing_disabled(True) # 关闭日志
    agent = create_agent(base_url='https://api.deepseek.com',
                 llm_name='deepseek-chat',
                 api_key='sk-3331653c2df04aafb6b4b4eb484f24d0',
                 agent_name='Intelligent Assistant',
                 agent_description='You are an intelligent assistant capable of chatting and calling tools.',
                 skill_dir='skills')
    result = run_agent(agent, prompt='帮我查一下北京的天气')
    print(result.final_output)
        