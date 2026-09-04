"""FastAPI 入口：CORS、路由挂载、启动命令。"""

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .agent import run_agent, run_agent_stream
from .schemas import ChatRequest, ChatResponse, HealthResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Personal Assistant Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse()


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply, trace = run_agent(req.message, req.history or None)
    return ChatResponse(reply=reply, trace=trace)


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            history = data.get("history", [])

            if not message.strip():
                await websocket.send_json({"type": "error", "message": "消息不能为空"})
                continue

            async for event in run_agent_stream(message, history or None):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
