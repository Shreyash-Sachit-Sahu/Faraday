"""Lazy-loaded Gemma 2 + LoRA adapter, prompt assembly, token streaming."""

import os

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

from app import config
from app.retrieval.retriever import retrieve  # Phase 2/3 pipeline

_MODEL = None
_TOKENIZER = None

SYSTEM = (
    "You are Faraday, a precise computer-science tutor. Use ONLY the context "
    "below when it is relevant, and cite passages as [1], [2] when you use "
    "them. If the context does not contain the answer, say so plainly and "
    "answer from general CS knowledge, noting the distinction. Be clear and "
    "pedagogical; include short code when it helps."
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


def build_prompt(tokenizer, query: str, chunks: list) -> str:
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
    user = f"{SYSTEM}{note}\n\nContext:\n{context}\n\nQuestion: {query}"
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


def make_streamer_and_kwargs(query: str, owner_ids: list[str] | None):
    import torch
    from transformers import TextIteratorStreamer

    model, tokenizer = _load()
    chunks = retrieve(
        query,
        k_final=6,
        use_graph=config.RETRIEVAL_USE_GRAPH,
        owner_ids=owner_ids or ["global"],
    )
    prompt = build_prompt(tokenizer, query, chunks)
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
    sources = [
        {"n": i + 1, "title": c.title, "source": c.source, "url": c.url,
         "score": round(float(c.score), 3)}
        for i, c in enumerate(chunks)
    ]

    def run():
        with torch.no_grad():
            model.generate(**gen_kwargs)

    return streamer, run, sources


def main() -> None:
    import sys
    import threading

    query = sys.argv[1] if len(sys.argv) > 1 else (
        "Explain how a B-tree differs from a binary search tree."
    )
    streamer, run, sources = make_streamer_and_kwargs(query, None)
    print("sources:")
    for src in sources:
        print(
            f"  [{src['n']}] {src['title']} "
            f"({src['source']}, score {src['score']})"
        )
    print("\nanswer:")
    thread = threading.Thread(target=run)
    thread.start()
    for token in streamer:
        print(token, end="", flush=True)
    thread.join()
    print()


if __name__ == "__main__":
    main()
