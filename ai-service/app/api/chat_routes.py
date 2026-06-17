"""SSE /chat endpoint: retrieve context, stream the tutor's answer (local or remote)."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import config
from app.api.retrieval_routes import GPU_EXECUTOR
from app.inference.generator import (
    make_local_run,
    retrieve_and_sources,
    stream_remote,
)

router = APIRouter()

_SENTINEL = object()


class Turn(BaseModel):
    role: str = Field(max_length=16)
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    owner_ids: list[str] = Field(default=["global"], max_length=2)
    history: list[Turn] = Field(default_factory=list, max_length=20)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    loop = asyncio.get_running_loop()
    history = [t.model_dump() for t in req.history]

    async def event_stream():
        try:
            # Retrieval always runs locally (embedder/reranker on the GPU executor).
            chunks, sources = await loop.run_in_executor(
                GPU_EXECUTOR, retrieve_and_sources, req.query, req.owner_ids, history
            )
            yield _sse("sources", {"sources": sources})

            if config.GEN_PROVIDER == "openai":
                # Remote model: stream content deltas over the network (no GPU).
                gen = stream_remote(req.query, chunks, history)
                while True:
                    token = await loop.run_in_executor(None, lambda: next(gen, _SENTINEL))
                    if token is _SENTINEL:
                        break
                    yield _sse("token", {"text": token})
            else:
                # Local Gemma: generate on the single GPU executor, feeding the streamer.
                streamer, run = await loop.run_in_executor(
                    GPU_EXECUTOR, make_local_run, req.query, chunks, history
                )
                gen_future = loop.run_in_executor(GPU_EXECUTOR, run)
                while True:
                    token = await loop.run_in_executor(None, lambda: next(streamer, _SENTINEL))
                    if token is _SENTINEL:
                        break
                    yield _sse("token", {"text": token})
                await gen_future

            yield _sse("done", {})
        except Exception as exc:  # surface a clean error event, never a 500 mid-stream
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
