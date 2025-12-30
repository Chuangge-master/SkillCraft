# SkillCraft

SkillCraft是一个基于LangChain的AI代理技能管理框架，允许您轻松创建、加载和管理AI代理的技能。该框架提供了动态技能加载、工具管理和聊天界面功能。

## 项目结构

```
SkillCraft/
├── skills/                  # 技能目录
│   └── tourism_recommendation/  # 旅游推荐技能示例
│       ├── SKILL.md         # 技能元数据
│       └── tools.py         # 技能工具实现
├── main.py                  # 主入口文件
├── skill_helper.py          # 技能加载和代理创建辅助函数
├── prompts.py               # 提示词模板
├── web_app.py               # Web应用入口文件
├── __init__.py              # 包初始化文件
├── .env.example             # 环境变量示例
├── .gitignore               # Git忽略文件
├── .python-version          # Python版本管理
├── pyproject.toml           # 项目配置
└── uv.lock                  # 依赖锁定文件
```

## 核心功能

- **动态技能加载**：从`skills`目录递归加载所有技能
- **技能元数据管理**：通过YAML格式的SKILL.md文件定义技能信息和工具列表
- **工具自动装饰**：自动为技能工具应用LangChain的`@tool`装饰器
- **LLM代理创建**：使用LangChain框架创建AI Agent
- **技能选择机制**：自动根据用户请求选择合适的技能
- **流式输出**：支持实时流式内容输出
- **模块化设计**：清晰的代码结构，便于扩展和维护

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

### 3. 运行应用

```bash
python main.py
```

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
when_to_use: 技能使用场景
tools:
  - tool_name_1
  - tool_name_2
---

技能详细说明
```

### 3. 编写技能工具实现（tools.py）

```python
def tool_name(param: str) -> str:
    """工具描述
    Args:
        param (str): 参数描述
    Returns:
        str: 工具返回结果
    """
    # 实现技能逻辑
    return f"工具2执行结果: {param}"
```

## 核心模块说明

### skill_helper.py

技能加载和代理创建辅助函数，负责：
- 从`skills`目录递归加载所有技能（SKILL.md）
- 解析技能元数据
- 动态加载tools.py中的工具函数并应用@tool装饰器
- 创建LangChain Agent
- 实现技能选择和执行逻辑
- 支持流式输出结果

### prompts.py

提示词模板文件，包含：
- `skill_choose_prompt`：技能选择助手的系统提示词
- `run_agent_prompt`：技能执行助手的系统提示词

### main.py

主入口文件，展示如何使用框架创建和运行AI代理。

### web_app.py

Web应用入口文件，提供Web聊天界面。

## 依赖要求

- Python >= 3.12
- langchain
- langchain_openai
- pyyaml
- python-dotenv
- streamlit >= 1.30.0

## 许可证

MIT