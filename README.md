# SkillCraft

SkillCraft是一个用于创建和管理AI代理技能的Python框架，允许您轻松扩展LLM代理的功能。

## 项目结构

```
SkillCraft/
├── skills/                  # 技能目录
│   └── get_weather/         # 天气查询技能示例
│       ├── SKILL.md         # 技能元数据
│       └── skill.py         # 技能实现
├── main.py                  # 主入口文件
├── skill_loader.py          # 技能加载器
├── skill_helper.py          # 代理创建和运行辅助函数
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

### 3. 运行示例

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

代理创建和运行辅助函数：
- `create_agent()`：创建带有所有加载技能的AI代理
- `run_agent()`：运行代理处理用户请求

### main.py

主入口文件，展示如何使用框架创建和运行AI代理。

## 依赖要求

- Python >= 3.12
- openai >= 2.14.0
- openai-agents >= 0.6.4
- pyyaml >= 6.0.3
- python-dotenv

## 许可证

MIT
