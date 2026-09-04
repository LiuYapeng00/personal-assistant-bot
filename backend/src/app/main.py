"""FastAPI 入口：CORS、路由挂载、启动命令。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent import run_agent
from .schemas import ChatRequest, ChatResponse, HealthResponse

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
