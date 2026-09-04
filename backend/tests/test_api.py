"""API 接口测试（TestClient，无需启动真实服务器）。"""

from fastapi.testclient import TestClient

from app import agent
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_returns_reply(monkeypatch):
    monkeypatch.setattr(agent, "chat", lambda messages: '{"final_answer": "你好！"}')
    resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "你好！"
    assert body["trace"] == []


def test_chat_with_tool_call(monkeypatch):
    responses = iter(
        [
            '{"thought": "需要算题", "action": "calculator", '
            '"action_input": {"expression": "1+2"}}',
            '{"final_answer": "结果是 3"}',
        ]
    )

    def fake_chat(messages):
        return next(responses)

    monkeypatch.setattr(agent, "chat", fake_chat)
    resp = client.post("/chat", json={"message": "计算 1+2"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "结果是 3"
    assert len(body["trace"]) == 1
    assert body["trace"][0]["tool"] == "calculator"


def test_chat_empty_message():
    resp = client.post("/chat", json={"message": ""})
    assert resp.status_code == 422


def test_chat_missing_message():
    resp = client.post("/chat", json={})
    assert resp.status_code == 422


def test_cors_headers(monkeypatch):
    monkeypatch.setattr(agent, "chat", lambda messages: '{"final_answer": "ok"}')
    resp = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
