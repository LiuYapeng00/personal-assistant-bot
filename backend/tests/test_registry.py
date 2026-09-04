"""工具注册表测试 —— 参数校验、异常兜底、动态描述。"""

from app import agent
from app.tools import TOOLS, registry


def test_registry_has_three_tools():
    assert set(registry.names()) == {
        "get_weather_by_city",
        "calculator",
        "search_notes",
    }


def test_to_funcs_matches_registry():
    assert set(TOOLS) == set(registry.names())
    for name in registry.names():
        assert TOOLS[name] == registry.get(name).func


def test_call_success_calculator():
    assert registry.call("calculator", {"expression": "1 + 2 * 3"}) == "7"


def test_call_missing_required_param():
    result = registry.call("calculator", {})
    assert "缺少必填参数" in result
    assert "expression" in result


def test_call_wrong_type_param():
    result = registry.call("calculator", {"expression": 123})
    assert "类型错误" in result


def test_call_kwargs_not_dict():
    result = registry.call("calculator", ["1+1"])
    assert "参数必须是对象" in result


def test_call_unknown_tool():
    result = registry.call("nope", {})
    assert "未知工具" in result
    assert "可用工具" in result


def test_call_internal_exception_becomes_text():
    # 除零在 calculator 内部会抛 ValueError，应转为可回传文本，不抛异常
    result = registry.call("calculator", {"expression": "1/0"})
    assert "执行失败" in result
    assert "除数不能为零" in result


def test_describe_all_lists_tools():
    desc = registry.describe_all()
    assert "get_weather_by_city" in desc
    assert "calculator" in desc
    assert "search_notes" in desc


def test_agent_does_not_crash_on_tool_error(monkeypatch):
    """工具执行失败时，ReAct 循环不崩溃，能继续给出最终回答。"""
    responses = iter(
        [
            '{"thought": "除零", "action": "calculator", "action_input": {"expression": "1/0"}}',
            '{"final_answer": "除数不能为零"}',
        ]
    )

    def fake_chat(messages):
        return next(responses)

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("计算 1/0")
    assert "执行失败" in trace[0]["result"] or "除数不能为零" in trace[0]["result"]
    assert reply == "除数不能为零"


def test_agent_missing_param_does_not_crash(monkeypatch):
    responses = iter(
        [
            '{"thought": "缺参", "action": "calculator", "action_input": {}}',
            '{"final_answer": "请提供表达式"}',
        ]
    )

    def fake_chat(messages):
        return next(responses)

    monkeypatch.setattr(agent, "chat", fake_chat)
    reply, trace = agent.run_agent("算一下")
    assert "缺少必填参数" in trace[0]["result"]
    assert reply == "请提供表达式"
