"""
DeepSeek 客户端封装（OpenAI 兼容接口）。

只负责两件事：
1. 调用 DeepSeek 拿到模型文本（非流式，供 ReAct 决策使用）
2. 把模型输出的文本宽松解析成结构化决策（thought / action / action_input / final_answer）
"""

import json
import re

from openai import OpenAI

from . import config
from .tools import registry

_client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)

# 固定描述 ReAct 输出格式的 system prompt（可用工具由注册表动态生成）
SYSTEM_PROMPT = f"""你是一个乐于助人的个人助理。
你可以调用以下工具来回答用户的问题，工具以 JSON 对象返回结果，你也只输出 JSON。

可用工具：
{registry.describe_all()}

你必须严格按下面的 JSON 之一输出，不要输出任何多余文字：

如果还需要调用工具，输出：
{{"thought": "你的思考", "action": "工具名", "action_input": {{"key": "value"}}}}

如果已经有把握回答用户，输出：
{{"final_answer": "给用户的最终回答"}}

注意：
- action 必须是上面列出的工具名之一
- action_input 的字段必须符合该工具的要求
- 每次只输出一个 JSON
"""

# 轮数上限与超时（秒）
MAX_ROUNDS = 5
REQUEST_TIMEOUT = 30


def chat(messages: list[dict]) -> str:
    """调用 DeepSeek 非流式接口，返回文本内容。"""
    resp = _client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        temperature=0.3,
        timeout=REQUEST_TIMEOUT,
    )
    return (resp.choices[0].message.content or "").strip()


def extract_json(text: str) -> dict:
    """
    从模型输出里宽松提取 JSON。

    策略：
    1. 如果整段就是合法 JSON，直接解析。
    2. 否则用正则找第一个 {...} 花括号块（模型可能夹杂解释文字）。
    3. 找不到则抛 ValueError。
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"模型输出中没有找到 JSON：{text!r}")
    return json.loads(match.group(0))


def parse_decision(text: str) -> dict:
    """
    把模型文本解析为 ReAct 决策。

    返回:
      {"type": "final", "answer": "..."}        最终回答
      {"type": "action", "thought": "...", "tool": "...", "input": {...}}  调用工具
      {"type": "error", "message": "..."}        解析失败

    不会抛异常。
    """
    try:
        data = extract_json(text)
    except ValueError as e:
        return {"type": "error", "message": str(e)}

    if not isinstance(data, dict):
        return {"type": "error", "message": "JSON 不是对象"}

    if "final_answer" in data and data["final_answer"]:
        return {"type": "final", "answer": str(data["final_answer"])}

    if "action" in data and data["action"]:
        return {
            "type": "action",
            "thought": str(data.get("thought", "")),
            "tool": str(data["action"]),
            "input": data.get("action_input", {}) or {},
        }

    return {"type": "error", "message": f"JSON 缺少 final_answer 或 action：{data}"}
