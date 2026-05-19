# app/backend/routes.py
# All route definitions — /chat, /modes, /health

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.backend.llm import get_chat_reply, get_modes

router = APIRouter()

# ── Request / Response schemas ────────────────────────────────
class Message(BaseModel):
    role: str        # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]
    mode: str = "assistant"
    max_tokens: int = 512

class ChatResponse(BaseModel):
    reply: str

class ModesResponse(BaseModel):
    modes: list[str]

# ── Routes ────────────────────────────────────────────────────
@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/modes", response_model=ModesResponse)
def modes():
    return ModesResponse(modes=get_modes())


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        reply = get_chat_reply(messages, req.mode, req.max_tokens)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))