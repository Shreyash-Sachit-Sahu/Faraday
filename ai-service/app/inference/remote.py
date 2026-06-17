"""Streaming client for any OpenAI-compatible chat-completions API.

Used when GEN_PROVIDER=openai. Works with Groq and Google Gemini (free tiers),
OpenAI, OpenRouter, a local Ollama, etc. — point GEN_REMOTE_BASE_URL/MODEL/API_KEY
at the provider. Uses only the stdlib so it adds no dependencies.
"""

import json
import urllib.request
from typing import Iterable, Iterator

from app import config


def iter_sse_deltas(lines: Iterable) -> Iterator[str]:
    """Parse an OpenAI streaming response body into content deltas.

    Pure (no network) so it is unit-testable: accepts an iterable of SSE lines
    (bytes or str) and yields the text of each ``choices[0].delta.content``.
    """
    for raw in lines:
        line = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else raw
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            choices = json.loads(payload).get("choices") or []
            delta = (choices[0].get("delta") or {}).get("content") if choices else None
        except Exception:
            continue
        if delta:
            yield delta


def stream_chat_completion(messages: list[dict]) -> Iterator[str]:
    """Stream content deltas from the configured OpenAI-compatible endpoint."""
    if not config.GEN_REMOTE_MODEL or not config.GEN_REMOTE_API_KEY:
        raise RuntimeError(
            "GEN_PROVIDER=openai requires GEN_REMOTE_MODEL and GEN_REMOTE_API_KEY"
        )
    body = {
        "model": config.GEN_REMOTE_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": config.GEN_TEMPERATURE,
        "top_p": config.GEN_TOP_P,
        "max_tokens": config.GEN_MAX_NEW_TOKENS,
    }
    req = urllib.request.Request(
        config.GEN_REMOTE_BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {config.GEN_REMOTE_API_KEY}")
    resp = urllib.request.urlopen(req, timeout=120)
    yield from iter_sse_deltas(resp)
