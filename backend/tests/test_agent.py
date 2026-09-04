"""ReAct 主循环测试（mock DeepSeek，验证循环终止与轮数上限）。"""

import pytest

from app import agent


def test_final_answer_returns_directly(monkeypatch):
    monkeypatch.setattr(agent, "chat", lambda messages: '{"final_answer": "你好！"}')
    reply, trace = agent.run_agent("hi")
    assert reply == "你好！"
    assert trace == []


def test_agent_calls_tool_then_answers(monkeypatch):
    responses = iter(
        [
            '{"thought": "需要算题", "action": "calculator", '
            '"action_input": {"expression": "1+2*3"}}',
            '{"final_answer": "结果是 7"}',
        ]
    )

    def fake_chat(messages):
        return next(responses)

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("计算 1+2乘3")
    assert reply == "结果是 7"
    assert len(trace) == 1
    assert trace[0]["tool"] == "calculator"
    assert trace[0]["result"] == "7"


def test_unknown_tool_becomes_observation(monkeypatch):
    responses = iter(
        [
            '{"thought": "调用未知工具", "action": "nope", "action_input": {}}',
            '{"final_answer": "工具不可用"}',
        ]
    )

    def fake_chat(messages):
        return next(responses)

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("试试")
    # 未知工具应作为 Observation 回传，不至于崩溃
    assert "未知工具" in trace[0]["result"]
    assert reply == "工具不可用"


def test_max_rounds_cap(monkeypatch):
    # 模型永远要求调用工具，agent 应在 MAX_ROUNDS 轮后停止
    def fake_chat(messages):
        return '{"thought": "继续", "action": "calculator", "action_input": {"expression": "1+1"}}'

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("一直算")
    assert len(trace) == agent.MAX_ROUNDS
    assert "步骤过多" in reply


def test_parse_error_retries_once_then_fallback(monkeypatch):
    # 连续两次解析失败：第一次提示重试，第二次直接兜底
    responses = ["这不是json", "还能更乱"]
    call_count = 0

    def fake_chat(messages):
        nonlocal call_count
        call_count += 1
        return responses[call_count - 1]

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("测试容错")
    assert call_count == 2
    assert "无法理解" in reply


def test_parse_error_recovers_after_retry(monkeypatch):
    # 第一次解析失败，提示重试后模型恢复给出回答
    responses = ["这不是json", '{"final_answer": "挽救成功"}']
    call_count = 0

    def fake_chat(messages):
        nonlocal call_count
        call_count += 1
        return responses[call_count - 1]

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("测试容错")
    assert reply == "挽救成功"
    assert call_count == 2


def test_calculator_tool_basic():
    from app.tools.calculator import calculator

    assert calculator("1 + 2 * 3") == "7"
    assert calculator("10 / 2") == "5"


def test_calculator_invalid_raises():
    from app.tools.calculator import calculator

    with pytest.raises(ValueError):
        calculator("__import__('os').system('x')")
    with pytest.raises(ValueError):
        calculator("1 / 0")
