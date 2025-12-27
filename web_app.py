from dotenv import load_dotenv
import os
from skill_helper import create_agent_system, chat_with_agent_web


def main():
    # 加载环境变量
    load_dotenv()
    
    # 获取环境变量
    base_url = str(os.getenv('BASE_URL'))
    llm_name = str(os.getenv('LLM_NAME'))
    api_key = str(os.getenv('API_KEY'))
    
    # 创建Agent系统
    agent_system = create_agent_system(
        skill_dir='skills',
        base_url=base_url,
        llm_name=llm_name,
        api_key=api_key,
        force_reload=True
    )
    
    # 启动Web聊天服务
    chat_with_agent_web(agent_system)


if __name__ == "__main__":
    main()