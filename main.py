import dotenv
import os
from skill_helper import create_agent, run_agent

if __name__ == "__main__":
    
    dotenv.load_dotenv()

    agent = create_agent(base_url=str(os.getenv('BASE_URL')),
                 llm_name=str(os.getenv('LLM_NAME')),
                 api_key=str(os.getenv('API_KEY')),
                 agent_name='Intelligent Assistant',
                 agent_description='You are an intelligent assistant capable of chatting and calling tools.',
                 skill_dir='skills')
    result = run_agent(agent, prompt='你好，现在的你可以做什么？')
    print(result.final_output)
