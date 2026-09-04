"""Pydantic 请求/响应模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict[str, str]] = []


class TraceStep(BaseModel):
    step: int
    thought: str
    tool: str
    input: Any
    result: str


class ChatResponse(BaseModel):
    reply: str
    trace: list[TraceStep]


class HealthResponse(BaseModel):
    status: str = "ok"
