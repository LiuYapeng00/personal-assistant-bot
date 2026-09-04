# Backend

FastAPI 后端，基于 ReAct 循环的个人助理 Bot。

## 快速启动

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## 测试

```bash
uv run pytest tests/ -v      # 35 个测试
uv run ruff check src/ tests/ # lint
```

## 环境变量

复制 `.env.example` 为 `.env`，填入 DeepSeek API Key。

## API

- `GET /health` - 健康检查
- `POST /chat` - 非流式聊天
- `WS /ws/chat` - 流式聊天（WebSocket）
