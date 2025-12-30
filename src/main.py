import asyncio
from skill_helper import chat
import os

def main():
    import dotenv
    dotenv.load_dotenv('../.env')
    base_url = os.getenv("BASE_URL")
    llm_name = os.getenv("LLM_NAME")
    api_key = os.getenv("API_KEY")
    
    user_input = input("请输入你的问题：")
    chat(user_input, skill_dir='skills', base_url=base_url, llm_name=llm_name, api_key=api_key)
    

if __name__ == "__main__":
    main()
    
    
