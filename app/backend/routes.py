from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.backend.config import openai_configured
from app.backend.llm import stream_chat_reply
from app.backend.search import web_search
from app.shared.chat_presets import get_modes, should_use_search

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    mode: str = "assistant"
    max_tokens: int = 512
    engine: str = "duckduckgo"
    force_search: bool = False


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    engine: str = "duckduckgo"
    max_results: int = Field(default=3, ge=1, le=10)


@router.get("/health")
def health():
    return {
        "status": "ok",
        "openai_configured": openai_configured(),
    }


@router.get("/modes")
def modes():
    return {"modes": get_modes()}


@router.post("/search")
def search(req: SearchRequest):
    """Direct web search (for testing and sidebar preview)."""
    try:
        text = web_search(req.query, engine=req.engine, max_results=req.max_results)
        return {"query": req.query, "engine": req.engine, "results": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/search")
def search_get(
    q: str = Query(..., min_length=1),
    engine: str = "duckduckgo",
    max_results: int = Query(3, ge=1, le=10),
):
    try:
        text = web_search(q, engine=engine, max_results=max_results)
        return {"query": q, "engine": engine, "results": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/chat")
def chat(req: ChatRequest):
    if not openai_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY is not set. Create a .env file in the project root "
                "(copy from .env.example) with your key from "
                "https://platform.openai.com/api-keys — then restart the backend."
            ),
        )
    try:
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        last_msg = messages[-1]["content"] if messages else ""
        search_will_run = should_use_search(req.mode, last_msg, req.force_search)

        def stream_with_meta():
            if search_will_run:
                yield "[searching the web…]\n\n"
            yield from stream_chat_reply(
                messages,
                req.mode,
                req.max_tokens,
                req.engine,
                req.force_search,
            )

        return StreamingResponse(
            stream_with_meta(),
            media_type="text/plain",
            headers={"X-Search-Used": "true" if search_will_run else "false"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
