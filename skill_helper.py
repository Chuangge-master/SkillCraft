from agents import (Agent, RunResultStreaming,
    Runner,RunResult,OpenAIChatCompletionsModel,
    set_tracing_disabled,
    SQLiteSession,Session)
from openai import AsyncOpenAI
from skill_loader import SkillLoader
from openai.types.responses import ResponseTextDeltaEvent
import uuid
import os

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

def run_agent(agent: Agent, prompt: str, session_id: str = None) -> RunResult:
    set_tracing_disabled(True) # 关闭日志
    session = SQLiteSession(session_id, db_path=f"{session_id}.db") if session_id else None
    result = Runner.run_sync(agent, prompt, session=session)
    return result

async def run_agent_async(agent: Agent, prompt: str, session_id: str = None) -> RunResult:
    set_tracing_disabled(True) # 关闭日志
    session = SQLiteSession(session_id, db_path=f"{session_id}.db") if session_id else None
    result = await Runner.run(agent, prompt, session=session)
    return result

async def run_agent_stream(agent: Agent, prompt: str, session_id: str = None) -> RunResultStreaming:
    set_tracing_disabled(True) # 关闭日志
    session = SQLiteSession(session_id, db_path=f"{session_id}.db") if session_id else None
    result = Runner.run_streamed(agent, prompt, session=session)
    return result

async def chat_with_agent(agent: Agent, use_old_session: bool = False) -> None:
    """
    与智能助手进行聊天，支持会话上下文。
    
    Args:
        agent: OpenAI Agent
        use_old_session: 是否使用旧会话上下文，默认False
    """
    set_tracing_disabled(True) # 关闭日志
    # 随机生成会话id
    session_id = 'chat_session'
    if not use_old_session and os.path.exists(f"{session_id}.db"):
        # 检查是否存在旧会话数据库文件，存在则删除
        os.remove(f"{session_id}.db")

    while True:
        print(f"AI Agent：你好，我是一个智能助手，我可以聊天，也可以执行一些任务。")
        prompt = input("你: ")
        if prompt.lower() == "exit":
            print(f"AI Agent：再见！")
            break

        result = await run_agent_stream(agent, prompt, session_id=session_id)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
        print("\n")
    


if __name__ == "__main__":
    pass
    
        