from agents import (Agent, RunResultStreaming,
    Runner,RunResult,OpenAIChatCompletionsModel,
    set_tracing_disabled,
    SQLiteSession,Session)
from openai import AsyncOpenAI
from skill_loader import SkillLoader
from openai.types.responses import ResponseTextDeltaEvent
from prompts import planner_prompt, run_task_prompt, evaluate_task_prompt
import uuid
import os
import json
import asyncio

class AgentSystem:
    """Agent系统类，包含三个核心agent：规划器、执行器和评估器"""
    def __init__(self, planner_agent: Agent, run_task_agent: Agent, evaluate_task_agent: Agent):
        self.planner_agent = planner_agent
        self.run_task_agent = run_task_agent
        self.evaluate_task_agent = evaluate_task_agent


def create_agent_system(skill_dir: str, 
                      base_url: str,
                      llm_name: str,
                      api_key: str,
                      force_reload: bool = False) -> AgentSystem:
    """
    创建agent系统，包含规划器、执行器和评估器三个agent
    
    Args:
        skill_dir: 技能目录
        base_url: OpenAI API基础URL
        llm_name: 模型名称
        api_key: API密钥
        force_reload: 是否强制重新加载技能
    
    Returns:
        AgentSystem对象，包含三个核心agent
    """
    skill_loader = SkillLoader(skill_dir)
    skill_loader.load_skills(force_reload=force_reload)
    agent_description = ""

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

    # 创建规划器agent
    planner_agent = Agent(
        name="智能助手",
        instructions=planner_prompt,
        model=OpenAIChatCompletionsModel(
            model=llm_name,
            openai_client=openai_client,
        ),
    )

    # 创建任务执行助手agent
    run_task_agent = Agent( 
        name="任务执行助手",
        instructions=run_task_prompt,
        model=OpenAIChatCompletionsModel(
            model=llm_name,
            openai_client=openai_client,
        ),
        tools=[skill.tool for skill in skill_loader.skills if skill.tool is not None], 
    )
    run_task_agent.tools.extend(skills_direct_run)

    # 创建任务评估助手agent
    evaluate_task_agent = Agent( 
        name="任务评估助手",
        instructions=evaluate_task_prompt,
        model=OpenAIChatCompletionsModel(
            model=llm_name,
            openai_client=openai_client,
        ),
    )

    return AgentSystem(planner_agent, run_task_agent, evaluate_task_agent)

# 常量定义
DEFAULT_SESSION_ID = "chat_session"
MAX_RETRY_ATTEMPTS = 3
SESSION_DIRECTORY = "sessions"


def _get_session(session_id: str = None) -> Session:
    """
    获取或创建会话对象
    
    Args:
        session_id: 会话ID
    
    Returns:
        Session对象或None
    """
    if not session_id:
        return None
    
    os.makedirs(SESSION_DIRECTORY, exist_ok=True)
    db_path = os.path.join(SESSION_DIRECTORY, f"{session_id}.db")
    return SQLiteSession(session_id, db_path=db_path)

def run_agent(agent: Agent, query: str, session_id: str = None) -> RunResult:
    """
    同步运行智能体
    
    Args:
        agent: 智能体对象
        query: 查询内容
        session_id: 会话ID
    
    Returns:
        RunResult对象
    """
    set_tracing_disabled(True) # 关闭日志
    session = _get_session(session_id)
    result = Runner.run_sync(agent, query, session=session)
    return result

async def run_agent_async(agent: Agent, query: str, session_id: str = None) -> RunResult:
    """
    异步运行智能体
    
    Args:
        agent: 智能体对象
        query: 查询内容
        session_id: 会话ID
    
    Returns:
        RunResult对象
    """
    set_tracing_disabled(True) # 关闭日志
    session = _get_session(session_id)
    result = await Runner.run(agent, query, session=session)
    return result

async def run_agent_stream(agent: Agent, query: str, session_id: str = None) -> RunResultStreaming:
    """
    流式运行智能体
    
    Args:
        agent: 智能体对象
        query: 查询内容
        session_id: 会话ID
    
    Returns:
        RunResultStreaming对象
    """
    set_tracing_disabled(True) # 关闭日志
    session = _get_session(session_id)
    result = Runner.run_streamed(agent, query, session=session)
    return result

async def chat_with_agent(agent_system: AgentSystem, use_old_session: bool = False, session_id: str = None) -> None:
    """
    与智能助手进行聊天，支持会话上下文和任务执行。
    内部使用三个agent编排：规划器、执行器和评估器
    
    Args:
        agent_system: Agent系统，包含三个核心agent
        use_old_session: 是否使用旧会话上下文，默认False
        session_id: 自定义会话ID，默认自动生成
    """
    set_tracing_disabled(True) # 关闭日志
    
    # 生成或使用会话id
    if not session_id:
        session_id = DEFAULT_SESSION_ID if use_old_session else str(uuid.uuid4())
    
    # 确保会话数据库目录存在
    os.makedirs(SESSION_DIRECTORY, exist_ok=True)
    db_path = os.path.join(SESSION_DIRECTORY, f"{session_id}.db")
    
    # 如果不使用旧会话且会话文件存在，则删除
    if not use_old_session and session_id == DEFAULT_SESSION_ID and os.path.exists(db_path):
        os.remove(db_path)

    print("AI Agent：你好，我是一个智能助手，我可以聊天，也可以执行一些任务。")
    print("AI Agent：输入'exit'退出会话。")
    print("=" * 50)

    while True:
        prompt = input("你: ").strip()
        if prompt.lower() == "exit":
            print(f"AI Agent：再见！👋")
            break

        if not prompt:
            print("请输入内容")
            continue

        # 第一阶段：规划器判断是聊天还是执行任务
        print("\nAI Agent（规划）：", end=" ", flush=True)
        
        try:
            # 调用规划器agent，使用流式输出
            plan_result = await run_agent_stream(agent_system.planner_agent, prompt, session_id=session_id)
            plan_content = ""
            response_received = False
            
            async for event in plan_result.stream_events():
                try:
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        print(event.data.delta, end="", flush=True)
                        plan_content += event.data.delta
                        response_received = True
                except Exception as e:
                    # 处理单个事件的错误
                    print(f"[规划流错误: {str(e)}]", end="", flush=True)
            
            print()  # 换行
            
            if not response_received or not plan_content:
                print("规划器未返回结果，我将尝试直接回复。")
                await handle_chat(agent_system, prompt, session_id)
                continue
            
            # 尝试解析JSON
            try:
                plan_json = json.loads(plan_content)
                
                # 验证JSON结构
                if not isinstance(plan_json, dict):
                    print("规划结果不是有效的JSON对象，我将尝试直接回复。")
                    await handle_chat(agent_system, prompt, session_id)
                    continue
                
                task_plans = plan_json.get("task_plans", [])
                
                if task_plans and isinstance(task_plans, list):
                    # 是任务执行请求
                    print("\n我需要执行以下任务：")
                    for i, task_plan in enumerate(task_plans):
                        if isinstance(task_plan, dict) and "task" in task_plan:
                            print(f"{i+1}. {task_plan['task']}")
                        else:
                            print(f"{i+1}. 任务格式错误")
                    
                    # 执行任务
                    await execute_task_plan(agent_system, task_plans, session_id)
                else:
                    # 任务计划为空或格式错误，可能是聊天
                    print("\n这是一个聊天请求，我将直接回复。")
                    await handle_chat(agent_system, prompt, session_id)
                    
            except json.JSONDecodeError as e:
                # 不是JSON格式，说明是聊天请求
                print(f"\n规划结果不是JSON格式（{str(e)}），我将尝试直接回复。")
                await handle_chat(agent_system, prompt, session_id)
                
        except Exception as e:
            print(f"\n发生错误：{str(e)}")
            print("我将尝试直接回复您的请求。")
            await handle_chat(agent_system, prompt, session_id)
            continue
        
        print("=" * 50)

async def handle_chat(agent_system: AgentSystem, prompt: str, session_id: str) -> None:
    """
    处理聊天请求
    
    Args:
        agent_system: Agent系统
        prompt: 用户输入
        session_id: 会话ID
    """
    print("AI Agent（聊天）：", end="", flush=True)
    
    try:
        result = await run_agent_stream(agent_system.planner_agent, prompt, session_id=session_id)
        response_received = False
        
        async for event in result.stream_events():
            try:
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
                    response_received = True
            except Exception as e:
                # 处理单个事件的错误
                print(f"[流错误: {str(e)}]", end="", flush=True)
        
        if not response_received:
            print("[未收到响应]")
        print("\n")
        
    except Exception as e:
        # 处理流初始化错误
        print(f"[聊天错误: {str(e)}]")
        print("\n")
        import traceback
        traceback.print_exc()

async def execute_task_plan(agent_system: AgentSystem, task_plans: list, session_id: str) -> None:
    """
    执行任务计划
    
    Args:
        agent_system: Agent系统
        task_plans: 任务计划列表
        session_id: 会话ID
    """
    print("\n开始执行任务计划...")
    
    # 确保任务计划格式正确
    validated_task_plans = []
    for i, task_plan in enumerate(task_plans):
        if isinstance(task_plan, dict):
            # 确保必要字段存在
            validated_task = {
                "step": task_plan.get("step", str(i+1)),
                "task": task_plan.get("task", ""),
                "task_result": task_plan.get("task_result", ""),
                "is_complete": task_plan.get("is_complete", False),
                "error_message": task_plan.get("error_message", "")
            }
            validated_task_plans.append(validated_task)
        else:
            print(f"\n❌ 任务 {i+1} 格式错误：{task_plan}")
            return
    
    # 遍历每个任务
    for i, task_plan in enumerate(validated_task_plans):
        print(f"\n任务 {i+1}/{len(validated_task_plans)}：{task_plan['task']}")
        
        # 重置任务状态
        current_task = {
            "step": task_plan["step"],
            "task": task_plan["task"],
            "task_result": task_plan["task_result"],
            "is_complete": False,
            "error_message": ""
        }
        
        # 最多尝试次数
        max_attempts = MAX_RETRY_ATTEMPTS
        task_completed = False
        
        for attempt in range(max_attempts):
            print(f"  尝试 {attempt+1}/{max_attempts}：", end="", flush=True)
            
            try:
                # 调用任务执行助手
                execute_result = await run_agent_async(
                    agent_system.run_task_agent, 
                    json.dumps(current_task, ensure_ascii=False, indent=2), 
                    session_id=session_id
                )
                
                execute_content = execute_result.final_output.strip() if execute_result.final_output else ""
                if not execute_content:
                    print("❌ 执行助手未返回结果")
                    current_task["error_message"] = "执行助手未返回结果"
                    continue
                
                # 解析执行结果
                try:
                    execute_json = json.loads(execute_content)
                except json.JSONDecodeError as e:
                    print(f"❌ 执行结果解析错误：{str(e)}")
                    print(f"  原始结果：{execute_content[:100]}...")
                    current_task["error_message"] = f"执行结果格式错误：{str(e)}"
                    continue
                
                # 确保执行结果格式正确
                if not isinstance(execute_json, dict):
                    print("❌ 执行结果格式错误")
                    current_task["error_message"] = "执行结果不是有效的JSON对象"
                    continue
                
                # 更新当前任务状态
                current_task = {
                    "step": execute_json.get("step", current_task["step"]),
                    "task": execute_json.get("task", current_task["task"]),
                    "task_result": execute_json.get("task_result", ""),
                    "is_complete": execute_json.get("is_complete", False),
                    "error_message": execute_json.get("error_message", "")
                }
                
                # 调用任务评估助手
                evaluate_result = await run_agent_async(
                    agent_system.evaluate_task_agent, 
                    json.dumps(current_task, ensure_ascii=False, indent=2), 
                    session_id=session_id
                )
                
                evaluate_content = evaluate_result.final_output.strip() if evaluate_result.final_output else ""
                if not evaluate_content:
                    print("❌ 评估助手未返回结果")
                    current_task["error_message"] = "评估助手未返回结果"
                    continue
                
                # 解析评估结果
                try:
                    evaluate_json = json.loads(evaluate_content)
                except json.JSONDecodeError as e:
                    print(f"❌ 评估结果解析错误：{str(e)}")
                    print(f"  原始结果：{evaluate_content[:100]}...")
                    current_task["error_message"] = f"评估结果格式错误：{str(e)}"
                    continue
                
                # 确保评估结果格式正确
                if not isinstance(evaluate_json, dict):
                    print("❌ 评估结果格式错误")
                    current_task["error_message"] = "评估结果不是有效的JSON对象"
                    continue
                
                if evaluate_json.get("is_complete", False):
                    print("✅ 完成")
                    result_preview = evaluate_json.get("task_result", "")[:100] + "..." if len(evaluate_json.get("task_result", "")) > 100 else evaluate_json.get("task_result", "")
                    print(f"  结果：{result_preview}")
                    validated_task_plans[i] = evaluate_json
                    task_completed = True
                    break
                else:
                    print("❌ 未完成")
                    error_msg = evaluate_json.get("error_message", "未提供原因")
                    print(f"  原因：{error_msg}")
                    # 更新当前任务状态，用于下一次尝试
                    current_task = {
                        "step": evaluate_json.get("step", current_task["step"]),
                        "task": evaluate_json.get("task", current_task["task"]),
                        "task_result": evaluate_json.get("task_result", current_task["task_result"]),
                        "is_complete": False,
                        "error_message": error_msg
                    }
                    
            except Exception as e:
                print(f"❌ 执行错误：{str(e)}")
                current_task["error_message"] = str(e)
                import traceback
                traceback.print_exc()
                
            # 等待一小段时间后重试
            if attempt < max_attempts - 1:
                print("\n  准备重试...")
                await asyncio.sleep(1)
        
        if not task_completed:
            # 所有尝试都失败
            print(f"\n  ⚠️  任务执行失败（已尝试{max_attempts}次）")
            validated_task_plans[i]["error_message"] = current_task.get("error_message", "未知错误")
            validated_task_plans[i]["is_complete"] = False
    
    # 更新原始任务计划
    for i, task_plan in enumerate(validated_task_plans):
        if i < len(task_plans):
            task_plans[i] = task_plan
    
    # 总结任务执行结果
    print("\n任务执行总结：")
    all_completed = True
    failed_tasks = []
    
    for i, task_plan in enumerate(validated_task_plans):
        if task_plan.get("is_complete", False):
            print(f"✅ 任务 {i+1}：完成")
        else:
            error_msg = task_plan.get("error_message", "未知错误")
            print(f"❌ 任务 {i+1}：失败 - {error_msg}")
            all_completed = False
            failed_tasks.append((i+1, task_plan['task'], error_msg))
    
    if all_completed:
        print("\n🎉 所有任务执行完成！")
    else:
        print("\n⚠️  部分任务执行失败。")
        if failed_tasks:
            print("\n失败详情：")
            for task_num, task_desc, error_msg in failed_tasks:
                print(f"- 任务 {task_num}：{task_desc}")
                print(f"  失败原因：{error_msg}")
    


if __name__ == "__main__":
    # 测试用例：简单的任务计划执行
    try:
        # 创建Agent系统
        agent_system = create_agent_system(
            skill_dir="skills",
            base_url="http://localhost:11434/v1",  # 假设使用Ollama本地服务
            llm_name="llama3",
            api_key="ollama",  # Ollama不需要真实API密钥
            force_reload=True
        )
        
        print("Agent系统创建成功！")
        print("开始测试聊天功能...")
        
        # 由于这是测试，我们不会真正启动交互式聊天
        # 而是模拟一个简单的调用
        print("\n测试完成！")
        
    except Exception as e:
        print(f"测试失败：{str(e)}")
        import traceback
        traceback.print_exc()
    
        