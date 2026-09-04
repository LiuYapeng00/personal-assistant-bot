"""ReAct 主循环：推理 - 行动 - 观察，直到给出最终回答或达到轮数上限。"""

from collections.abc import AsyncGenerator

from .llm import MAX_ROUNDS, SYSTEM_PROMPT, chat, chat_stream, parse_decision
from .tools import registry


def _run_tool(tool: str, tool_input) -> str:
    """执行工具并统一返回字符串结果；调用注册表完成校验、执行与异常兜底。"""
    return registry.call(tool, tool_input if isinstance(tool_input, dict) else {})


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


async def run_agent_stream(
    user_message: str, history: list | None = None
) -> AsyncGenerator[dict, None]:
    """
    流式 ReAct 循环 — 异步生成器，逐事件 yield JSON。

    事件类型：
      tool_call   — 工具调用开始（同步收集完整 JSON 后发出）
      tool_result — 工具返回结果
      token       — 最终回答的文本片段（逐 token 流式）
      done        — 流结束，附带完整回答
      error       — 错误
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    trace = []
    retry_after_parse_error = False

    for step in range(1, MAX_ROUNDS + 1):
        # 同步收集完整文本（ReAct 决策需要完整 JSON）
        raw = "".join(chat_stream(messages))
        decision = parse_decision(raw)

        if decision["type"] == "final":
            answer = decision["answer"]
            # 流式输出最终回答
            for token in answer:
                yield {"type": "token", "content": token}
            yield {"type": "done", "full_reply": answer}
            return

        if decision["type"] == "action":
            tool = decision["tool"]
            tool_input = decision["input"]

            yield {
                "type": "tool_call",
                "step": step,
                "thought": decision["thought"],
                "tool": tool,
                "input": tool_input,
            }

            observation = _run_tool(tool, tool_input)

            yield {"type": "tool_result", "step": step, "result": observation}

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

        yield {"type": "error", "message": "抱歉，我暂时无法理解你的问题，请换个问法。"}
        yield {"type": "done", "full_reply": ""}
        return

    yield {"type": "error", "message": "抱歉，处理步骤过多，已停止。请尝试换个更直接的问题。"}
    yield {"type": "done", "full_reply": ""}
