import dotenv
import os
from skill_helper import create_agent, run_agent, run_agent_stream, chat_with_agent
from openai.types.responses import ResponseTextDeltaEvent
import asyncio

async def main():
    dotenv.load_dotenv()

    agent = create_agent(base_url=str(os.getenv('BASE_URL')),
                 llm_name=str(os.getenv('LLM_NAME')),
                 api_key=str(os.getenv('API_KEY')),
                 agent_name='Intelligent Assistant',
                 agent_description='You are an intelligent assistant capable of chatting and calling tools.',
                 skill_dir='skills')

    # 运行代理
    # result = run_agent(agent, prompt='你好，现在的你可以做什么？')
    # print(result.final_output)

    # 流式输出
    result = await run_agent_stream(agent, prompt='你好，现在的你可以做什么？')
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

async def chat():
    dotenv.load_dotenv()

    agent = create_agent(base_url=str(os.getenv('BASE_URL')),
                 llm_name=str(os.getenv('LLM_NAME')),
                 api_key=str(os.getenv('API_KEY')),
                 agent_name='Intelligent Assistant',
                 agent_description='You are an intelligent assistant capable of chatting and calling tools.',
                 skill_dir='skills')

    await chat_with_agent(agent)

if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(chat())
    
    
