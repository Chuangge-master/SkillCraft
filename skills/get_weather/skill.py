from typing import Dict,Any
import json
from pydantic import BaseModel
from agents import RunContextWrapper, FunctionTool

class FunctionArgs(BaseModel):
    location: str

async def run(ctx: RunContextWrapper[Any], args:str) -> str:
    parsed = FunctionArgs.model_validate_json(args)
    return json.dumps({
        "location": parsed.location,
        "temperature": "20",
        "weather": "sunny"
    })