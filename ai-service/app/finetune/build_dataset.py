"""Step C: build the QLoRA SFT dataset (CS-leaning), tokenize, mask prompt tokens."""

import argparse
import json
import random
from typing import Any

from app import config
from app.pipeline.stage1_wikipedia import CS_KEYWORDS

TRAIN_NAME = "sft_train.jsonl"
EVAL_NAME = "sft_eval.jsonl"
EVAL_FRACTION = 0.05


def tokenize_example(example: dict, tokenizer, max_len: int) -> dict:
    """Gemma chat format; mask prompt tokens so loss is only on the response."""
    messages = [{"role": "user", "content": example["instruction"]}]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    full = prompt + example["response"] + tokenizer.eos_token

    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    full_ids = tokenizer(full, add_special_tokens=False)["input_ids"][:max_len]

    labels = list(full_ids)
    for i in range(min(len(prompt_ids), len(labels))):
        labels[i] = -100  # ignore prompt tokens in the loss

    return {
        "input_ids": full_ids,
        "attention_mask": [1] * len(full_ids),
        "labels": labels,
    }


def _is_cs(text: str) -> bool:
    low = text.lower()
    return any(keyword in low for keyword in CS_KEYWORDS)


def load_codealpaca(max_n: int) -> tuple[list[dict], str | None]:
    """Cached from Phase 1; map prompt/completion -> instruction/response."""
    try:
        from datasets import load_dataset

        rows = load_dataset("HuggingFaceH4/CodeAlpaca_20K", split="train")
    except Exception as exc:  # noqa: BLE001 — source must be optional
        return [], f"codealpaca unavailable: {exc}"
    out: list[dict] = []
    for row in rows:
        if len(out) >= max_n:
            break
        instruction = (row["prompt"] or "").strip()
        response = (row["completion"] or "").strip()
        if instruction and response:
            out.append({"instruction": instruction, "response": response})
    return out, None


def load_alpaca(max_n: int) -> tuple[list[dict], str | None]:
    """Prefer CS/technical rows; fold non-empty input; backfill with general rows."""
    try:
        from datasets import load_dataset

        rows = load_dataset("tatsu-lab/alpaca", split="train")
    except Exception as exc:  # noqa: BLE001 — source must be optional
        return [], f"alpaca unavailable: {exc}"
    cs_rows: list[dict] = []
    general_rows: list[dict] = []
    for row in rows:
        instruction = (row["instruction"] or "").strip()
        input_text = (row.get("input") or "").strip()
        response = (row.get("output") or "").strip()
        if not instruction or not response:
            continue
        if input_text:
            instruction = instruction + "\n\n" + input_text
        item = {"instruction": instruction, "response": response}
        (cs_rows if _is_cs(instruction) else general_rows).append(item)
    out = cs_rows[:max_n]
    if len(out) < max_n:
        out += general_rows[: max_n - len(out)]
    return out, None


def load_lima(max_n: int) -> tuple[list[dict], str | None]:
    """First turn only; gated like Gemma — skip and report if unavailable."""
    try:
        from datasets import load_dataset

        rows = load_dataset("GAIR/lima", split="train")
    except Exception as exc:  # noqa: BLE001 — source must be optional
        return [], f"lima unavailable: {exc}"
    out: list[dict] = []
    for row in rows:
        if len(out) >= max_n:
            break
        conv = row.get("conversations") or []
        if len(conv) >= 2:
            instruction = (conv[0] or "").strip()
            response = (conv[1] or "").strip()
            if instruction and response:
                out.append({"instruction": instruction, "response": response})
    return out, None


def _length_stats(examples: list[dict], tokenizer, max_len: int) -> dict[str, Any]:
    """Untruncated tokenized lengths so the max_len cap can be judged."""
    import numpy as np

    lengths = []
    for ex in examples:
        messages = [{"role": "user", "content": ex["instruction"]}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        full = prompt + ex["response"] + tokenizer.eos_token
        lengths.append(len(tokenizer(full, add_special_tokens=False)["input_ids"]))
    arr = np.array(lengths)
    truncated = int((arr > max_len).sum())
    return {
        "min": int(arr.min()),
        "median": int(np.median(arr)),
        "p95": int(np.percentile(arr, 95)),
        "max": int(arr.max()),
        "truncated": truncated,
        "truncation_rate": round(truncated / len(arr), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the QLoRA SFT dataset.")
    parser.add_argument("--max-codealpaca", type=int, default=1800)
    parser.add_argument("--max-alpaca", type=int, default=1500)
    parser.add_argument("--max-lima", type=int, default=700)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-len", type=int, default=512)
    args = parser.parse_args()

    sources = {
        "codealpaca": load_codealpaca(args.max_codealpaca),
        "alpaca": load_alpaca(args.max_alpaca),
        "lima": load_lima(args.max_lima),
    }
    combined: list[dict] = []
    for name, (rows, shortfall) in sources.items():
        print(f"  {name}: kept {len(rows)}" + (f" ({shortfall})" if shortfall else ""))
        combined.extend(rows)

    seen: set[str] = set()
    deduped: list[dict] = []
    for item in combined:
        key = item["instruction"]
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    print(f"combined {len(combined)} -> deduped {len(deduped)}")

    random.Random(args.seed).shuffle(deduped)
    n_eval = max(1, int(len(deduped) * EVAL_FRACTION))
    eval_split = deduped[-n_eval:]
    train_split = deduped[:-n_eval]

    for name, split in [(TRAIN_NAME, train_split), (EVAL_NAME, eval_split)]:
        path = config.DATA_DIR / name
        with open(path, "w", encoding="utf-8") as handle:
            for item in split:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"wrote {len(split)} -> {path}")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(config.BASE_MODEL)
    stats = _length_stats(train_split, tokenizer, args.max_len)
    print(
        f"train token lengths: min={stats['min']} median={stats['median']} "
        f"p95={stats['p95']} max={stats['max']} | "
        f"truncated@{args.max_len}={stats['truncated']} "
        f"({stats['truncation_rate'] * 100:.1f}%)"
    )


if __name__ == "__main__":
    main()
