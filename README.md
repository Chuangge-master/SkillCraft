# SkillCraft

SkillCraft是一个用于创建和管理AI代理技能的Python框架，允许您轻松扩展LLM代理的功能。该框架现在支持Web聊天界面和三智能体协同流程，提供了更好的用户体验和更强大的功能。

## 项目结构

```
SkillCraft/
├── skills/                  # 技能目录
│   └── get_weather/         # 天气查询技能示例
│       ├── SKILL.md         # 技能元数据
│       └── skill.py         # 技能实现
├── main.py                  # 主入口文件（命令行版本）
├── skill_loader.py          # 技能加载器
├── skill_helper.py          # 代理创建和运行辅助函数，包含Web聊天界面实现
├── web_app.py               # Web应用入口文件（Streamlit）
├── __init__.py              # 包初始化文件
├── .gitignore               # Git忽略文件
├── .python-version          # Python版本管理
├── pyproject.toml           # 项目配置
└── uv.lock                  # 依赖锁定文件
```

## 核心功能

- **动态技能加载**：从`skills`目录自动加载所有技能
- **技能元数据管理**：通过YAML格式的SKILL.md文件定义技能信息
- **LLM代理创建**：使用openai-agents库创建AI Agent
- **技能执行**：支持异步执行技能函数
- **Web聊天界面**：基于Streamlit实现的交互式Web聊天界面
- **三智能体协同流程**：规划器（判断任务/聊天）→执行器（执行任务）→评估器（验证结果）
- **流式输出**：支持实时流式内容输出，提供更好的用户体验
- **会话管理**：支持多用户会话，保持聊天上下文
- **加载状态提示**：在AI代理调用期间显示spinner加载提示，避免用户误以为系统卡住

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建`.env`文件：

```
BASE_URL=https://api.example.com/v1
LLM_NAME=gpt-3.5-turbo
API_KEY=your-api-key
```

### 3. 运行命令行版本

```bash
python main.py
```

### 4. 运行Web应用

```bash
streamlit run web_app.py
```

然后在浏览器中访问显示的URL（通常是http://localhost:8501）

## 创建自定义技能

### 1. 创建技能目录

在`skills`目录下创建新的技能目录：

```bash
mkdir -p skills/your_skill_name
```

### 2. 编写技能元数据（SKILL.md）

```yaml
---
name: your_skill_name
description: 技能描述
how_to_use: 技能使用场景
---

技能详细说明
```

### 3. 编写技能实现（skill.py）

```python
from typing import Dict, Any
import json
from pydantic import BaseModel
from agents import RunContextWrapper

class FunctionArgs(BaseModel):
    # 定义技能参数
    param1: str
    param2: int = None

async def run(ctx: RunContextWrapper[Any], args: str) -> str:
    # 解析参数
    parsed = FunctionArgs.model_validate_json(args)
    
    # 实现技能逻辑
    result = {
        "param1": parsed.param1,
        "param2": parsed.param2,
        "output": "技能执行结果"
    }
    
    # 返回JSON格式的结果
    return json.dumps(result)
```

## 核心模块说明

### skill_loader.py

技能加载器，负责：
- 遍历`skills`目录
- 解析SKILL.md文件获取技能元数据
- 加载skill.py中的run函数
- 创建FunctionTool对象

### skill_helper.py

代理创建和运行辅助函数，现在包含：
- `create_agent()`：创建带有所有加载技能的AI代理
- `run_agent()`：运行代理处理用户请求（命令行版本）
- `run_agent_stream()`：运行代理并返回流式输出
- `run_agent_async()`：异步运行代理
- `chat_with_agent()`：处理控制台聊天请求，实现三智能体协同流程
- `chat_with_agent_web()`：处理Web聊天请求，实现三智能体协同流程

### main.py

主入口文件，展示如何使用框架创建和运行AI代理（命令行版本）。

### web_app.py

Web应用入口文件，基于Streamlit实现：
- 初始化Agent系统
- 启动Web聊天界面
- 处理用户输入和显示输出

## 三智能体协同流程

SkillCraft现在实现了三智能体协同流程，用于处理复杂任务：

1. **规划器**：判断用户请求是聊天还是任务，并生成任务计划
2. **执行器**：执行生成的任务计划
3. **评估器**：验证任务执行结果的正确性

这个流程在Web界面中通过加载状态提示（spinner）进行可视化，让用户清楚了解当前系统状态。

## 依赖要求

- Python >= 3.12
- openai >= 2.14.0
- openai-agents >= 0.6.4
- pyyaml >= 6.0.3
- python-dotenv
- streamlit >= 1.30.0

## 许可证

MIT