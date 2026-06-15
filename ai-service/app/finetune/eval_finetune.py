"""Step F: prove the adapter lowered held-out loss vs base, and eyeball the voice."""

import os

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

import argparse
import json
import sys
from pathlib import Path

from app import config
from app.finetune.build_dataset import tokenize_example

QUAL_PROMPTS = [
    "Explain how a hash table handles collisions.",
    "What is the time complexity of quicksort and why?",
    "Write a Python function that checks if a string is a palindrome.",
    "Explain the difference between TCP and UDP.",
    "What is a deadlock and how can it be prevented?",
]


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_base_and_adapter():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
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
    tokenizer = AutoTokenizer.from_pretrained(config.BASE_MODEL)
    return model, tokenizer


def _mean_completion_loss(model, tokenizer, rows: list[dict], max_len: int) -> float:
    """Token-weighted mean cross-entropy over completion (non-masked) tokens."""
    import torch

    total_loss = 0.0
    total_tokens = 0
    for example in rows:
        toks = tokenize_example(example, tokenizer, max_len)
        n_tokens = sum(1 for label in toks["labels"] if label != -100)
        if n_tokens == 0:
            continue
        input_ids = torch.tensor([toks["input_ids"]], device=model.device)
        attention_mask = torch.tensor([toks["attention_mask"]], device=model.device)
        labels = torch.tensor([toks["labels"]], device=model.device)
        with torch.no_grad():
            out = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
        total_loss += float(out.loss) * n_tokens
        total_tokens += n_tokens
    return total_loss / total_tokens if total_tokens else float("nan")


def _generate(model, tokenizer, prompt: str, max_new_tokens: int) -> str:
    import torch

    text = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False
        )
    return tokenizer.decode(
        out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the QLoRA adapter.")
    parser.add_argument("--max-len", type=int, default=512)
    parser.add_argument("--gen-tokens", type=int, default=200)
    parser.add_argument("--limit", type=int, default=0, help="cap eval rows (0=all)")
    args = parser.parse_args()

    model, tokenizer = _load_base_and_adapter()
    eval_rows = _read_jsonl(config.DATA_DIR / "sft_eval.jsonl")
    if args.limit:
        eval_rows = eval_rows[: args.limit]
    print(f"eval rows: {len(eval_rows)}")

    adapter_loss = _mean_completion_loss(model, tokenizer, eval_rows, args.max_len)
    with model.disable_adapter():
        base_loss = _mean_completion_loss(model, tokenizer, eval_rows, args.max_len)
    delta = adapter_loss - base_loss
    passed = adapter_loss <= base_loss

    print("\n=== qualitative (closed-book; adapter vs base) ===")
    for prompt in QUAL_PROMPTS:
        adapter_text = _generate(model, tokenizer, prompt, args.gen_tokens)
        with model.disable_adapter():
            base_text = _generate(model, tokenizer, prompt, args.gen_tokens)
        print(f"\n### {prompt}")
        print(f"[adapter] {adapter_text}")
        print(f"[base]    {base_text}")

    print(
        f"\nVERDICT: adapter_loss={adapter_loss:.4f} base_loss={base_loss:.4f} "
        f"delta={delta:+.4f} -> {'PASS' if passed else 'FAIL'} "
        f"(gate: adapter <= base)"
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
