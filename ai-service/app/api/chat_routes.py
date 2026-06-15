"""SSE /chat endpoint: retrieve context, stream the tutor's answer."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.retrieval_routes import GPU_EXECUTOR
from app.inference.generator import make_streamer_and_kwargs

router = APIRouter()

_SENTINEL = object()


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    owner_ids: list[str] = Field(default=["global"], max_length=2)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    loop = asyncio.get_running_loop()

    async def event_stream():
        try:
            streamer, run, sources = await loop.run_in_executor(
                GPU_EXECUTOR, make_streamer_and_kwargs, req.query, req.owner_ids
            )
            yield _sse("sources", {"sources": sources})

            # Start generation on the single GPU executor; it feeds the streamer.
            gen_future = loop.run_in_executor(GPU_EXECUTOR, run)

            while True:
                token = await loop.run_in_executor(
                    None, lambda: next(streamer, _SENTINEL)
                )
                if token is _SENTINEL:
                    break
                yield _sse("token", {"text": token})

            await gen_future
            yield _sse("done", {})
        except Exception as exc:  # surface a clean error event, never a 500 mid-stream
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
