"""ReAct 主循环：推理 - 行动 - 观察，直到给出最终回答或达到轮数上限。"""

from .llm import MAX_ROUNDS, SYSTEM_PROMPT, chat, parse_decision
from .tools import TOOLS


def _run_tool(tool: str, tool_input) -> str:
    """执行工具并统一返回字符串结果；工具不存在或异常都转为可回传的文本。"""
    func = TOOLS.get(tool)
    if func is None:
        return f"未知工具，可用工具：{', '.join(TOOLS)}"

    try:
        result = func(**(tool_input if isinstance(tool_input, dict) else {}))
        if isinstance(result, dict):
            return str(result)
        return str(result)
    except Exception as e:  # noqa: BLE001 - 工具异常统一转为 Observation
        return f"工具执行失败: {e}"


def run_agent(user_message: str, history: list | None = None) -> tuple[str, list]:
    """
    运行 ReAct 循环。
    :param user_message: 用户输入
    :param history: 之前的对话历史（list[{"role","content"}]）
    :return: (最终回答, 工具调用轨迹 trace)
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    trace = []
    retry_after_parse_error = False

    for step in range(1, MAX_ROUNDS + 1):
        raw = chat(messages)
        decision = parse_decision(raw)

        if decision["type"] == "final":
            return decision["answer"], trace

        if decision["type"] == "action":
            tool = decision["tool"]
            tool_input = decision["input"]
            observation = _run_tool(tool, tool_input)

            trace.append(
                {
                    "step": step,
                    "thought": decision["thought"],
                    "tool": tool,
                    "input": tool_input,
                    "result": observation,
                }
            )

            messages.append({"role": "assistant", "content": raw})
            observation_msg = f"工具 {tool} 返回结果（Observation）：\n{observation}\n请继续。"
            messages.append({"role": "user", "content": observation_msg})
            retry_after_parse_error = False
            continue

        # parse 失败：重试一次，之后兜底
        if not retry_after_parse_error:
            retry_after_parse_error = True
            messages.append({"role": "user", "content": "输出无法解析，请严格只输出一个 JSON。"})
            continue

        return "抱歉，我暂时无法理解你的问题，请换个问法。", trace

    return "抱歉，处理步骤过多，已停止。请尝试换个更直接的问题。", trace
