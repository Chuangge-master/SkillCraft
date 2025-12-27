import dotenv
import os
from skill_helper import create_agent_system, run_agent, run_agent_stream, chat_with_agent
from openai.types.responses import ResponseTextDeltaEvent
import asyncio

async def chat():
    dotenv.load_dotenv()

    # 创建Agent系统
    agent_system = create_agent_system(skill_dir='skills',
                              base_url=str(os.getenv('BASE_URL')),
                              llm_name=str(os.getenv('LLM_NAME')),
                              api_key=str(os.getenv('API_KEY')))

    # 使用Agent系统进行聊天
    await chat_with_agent(agent_system)

if __name__ == "__main__":
    asyncio.run(chat())
    
    
