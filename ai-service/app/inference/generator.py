"""Prompt assembly + generation dispatch.

Retrieval and prompt-building are light (no ML imports at module load, so the
pure helpers are unit-testable); the local Gemma 2 + LoRA adapter and torch are
imported lazily inside the functions that need them. GEN_PROVIDER selects local
generation (this module) or a remote OpenAI-compatible API (app.inference.remote).
"""

import os

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

from app import config

_MODEL = None
_TOKENIZER = None

SYSTEM = (
    "You are Faraday, a precise computer-science tutor. Use ONLY the context "
    "below when it is relevant, and cite passages as [1], [2] when you use "
    "them. If the context does not contain the answer, say so plainly and "
    "answer from general CS knowledge, noting the distinction. Continue the "
    "conversation naturally, building on the earlier turns. Be clear, thorough, "
    "and pedagogical; when the question calls for code, give a complete, "
    "correct example."
)


def _load():
    global _MODEL, _TOKENIZER
    if _MODEL is None:
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from peft import PeftModel

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        base = AutoModelForCausalLM.from_pretrained(
            config.BASE_MODEL,
            quantization_config=bnb,
            device_map={"": 0},
            attn_implementation="eager",
            torch_dtype=torch.bfloat16,
        )
        model = PeftModel.from_pretrained(base, str(config.ADAPTER_DIR))
        model.eval()
        _MODEL = model
        _TOKENIZER = AutoTokenizer.from_pretrained(config.BASE_MODEL)
    return _MODEL, _TOKENIZER


# --- shared prompt/query helpers (no heavy imports; unit-tested) -------------

def _last_by_role(history: list[dict], role: str) -> str:
    for turn in reversed(history):
        if str(turn.get("role", "")).lower() == role:
            return str(turn.get("content", ""))
    return ""


def retrieval_query(query: str, history: list[dict]) -> str:
    """Anchor anaphoric follow-ups with the running topic so retrieval doesn't
    drift to unrelated passages. The last assistant answer is the most reliable
    signal — it survives a chain of contentless follow-ups ('explain more' ->
    'show me the code') where the last user turn carries no topic of its own;
    the last user turn adds any new keywords (e.g. 'code')."""
    assistant = _last_by_role(history, "assistant")[:240]
    user = _last_by_role(history, "user")
    anchor = " ".join(p for p in (assistant, user) if p).strip()
    return f"{anchor} {query}".strip() if anchor else query


def _format_history(
    history: list[dict], max_turns: int = 3, max_chars: int = 600
) -> str:
    """Compact transcript of the last few turns for the local prompt."""
    lines = []
    for turn in history[-(max_turns * 2):]:
        role = "User" if str(turn.get("role", "")).lower() == "user" else "Tutor"
        content = " ".join(str(turn.get("content", "")).split())
        if len(content) > max_chars:
            content = content[:max_chars] + "…"
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _context_block(chunks: list) -> tuple[str, str]:
    """Numbered context passages + a low-confidence note when retrieval is thin."""
    low_conf = (not chunks) or (chunks[0].score < config.GEN_LOW_CONF_THRESHOLD)
    note = (
        " The retrieved context looks thin for this question, so rely more on "
        "general CS knowledge and say if you are unsure."
        if low_conf
        else ""
    )
    context = "\n\n".join(
        f"[{i + 1}] {c.title}\n{c.text}" for i, c in enumerate(chunks)
    ) or "(no relevant context retrieved)"
    return context, note


def build_prompt(
    tokenizer, query: str, chunks: list, history: list[dict] | None = None
) -> str:
    """Single-turn Gemma chat-template prompt for the local model."""
    history = history or []
    context, note = _context_block(chunks)
    convo = _format_history(history)
    convo_block = f"Conversation so far:\n{convo}\n\n" if convo else ""
    user = f"{SYSTEM}{note}\n\n{convo_block}Context:\n{context}\n\nQuestion: {query}"
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


def build_messages(
    query: str, chunks: list, history: list[dict] | None = None
) -> list[dict]:
    """OpenAI-style messages for a remote model: system + prior turns + the
    context-grounded question."""
    history = history or []
    context, note = _context_block(chunks)
    messages = [{"role": "system", "content": SYSTEM + note}]
    for turn in history[-6:]:
        role = "user" if str(turn.get("role", "")).lower() == "user" else "assistant"
        content = str(turn.get("content", "")).strip()
        if content:
            messages.append({"role": role, "content": content})
    messages.append(
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    )
    return messages


# --- retrieval + sources (GPU work: embedder/reranker) -----------------------

def retrieve_and_sources(
    query: str, owner_ids: list[str] | None, history: list[dict] | None = None
):
    from app.retrieval.retriever import retrieve  # lazy: pulls the ML stack

    history = history or []
    chunks = retrieve(
        retrieval_query(query, history),
        k_final=6,
        use_graph=config.RETRIEVAL_USE_GRAPH,
        owner_ids=owner_ids or ["global"],
    )
    sources = [
        {"n": i + 1, "title": c.title, "source": c.source, "url": c.url,
         "score": round(float(c.score), 3)}
        for i, c in enumerate(chunks)
    ]
    return chunks, sources


# --- local generation (GPU) --------------------------------------------------

def make_local_run(query: str, chunks: list, history: list[dict] | None = None):
    """Returns (streamer, run): iterate `streamer` for tokens while `run`
    drives model.generate on the GPU executor."""
    import torch
    from transformers import TextIteratorStreamer

    model, tokenizer = _load()
    prompt = build_prompt(tokenizer, query, chunks, history)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=60
    )
    gen_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=config.GEN_MAX_NEW_TOKENS,
        do_sample=True,
        temperature=config.GEN_TEMPERATURE,
        top_p=config.GEN_TOP_P,
        repetition_penalty=config.GEN_REPETITION_PENALTY,
    )

    def run():
        with torch.no_grad():
            model.generate(**gen_kwargs)

    return streamer, run


# --- remote generation (no GPU; network) -------------------------------------

def stream_remote(query: str, chunks: list, history: list[dict] | None = None):
    from app.inference import remote

    return remote.stream_chat_completion(build_messages(query, chunks, history))


def main() -> None:
    import sys
    import threading

    query = sys.argv[1] if len(sys.argv) > 1 else (
        "Explain how a B-tree differs from a binary search tree."
    )
    chunks, sources = retrieve_and_sources(query, None, [])
    print("sources:")
    for src in sources:
        print(f"  [{src['n']}] {src['title']} ({src['source']}, score {src['score']})")
    print(f"\nanswer ({config.GEN_PROVIDER}):")
    if config.GEN_PROVIDER == "openai":
        for token in stream_remote(query, chunks, []):
            print(token, end="", flush=True)
    else:
        streamer, run = make_local_run(query, chunks, [])
        thread = threading.Thread(target=run)
        thread.start()
        for token in streamer:
            print(token, end="", flush=True)
        thread.join()
    print()


if __name__ == "__main__":
    main()
