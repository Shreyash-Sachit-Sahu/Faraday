"""Build a deterministic evalset from multi-chunk Wikipedia docs."""

import argparse
import json
import random
from typing import Any

from app import config

OUT_NAME = "evalset.jsonl"
SEED = 42
MAX_DOCS = 200
QUERY_TEMPLATES = ("What is {}?", "How does {} work?")


def main() -> None:
    argparse.ArgumentParser(
        description="Build evalset.jsonl from Wikipedia chunks."
    ).parse_args()

    docs: dict[str, dict[str, Any]] = {}
    in_path = config.DATA_DIR / "chunks_wikipedia.jsonl"
    with open(in_path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            entry = docs.setdefault(row["doc_id"], {"title": row["title"], "ids": []})
            entry["ids"].append(row["id"])

    eligible = {doc_id: entry for doc_id, entry in docs.items() if len(entry["ids"]) >= 2}
    sample_size = min(MAX_DOCS, len(eligible))
    sampled = random.Random(SEED).sample(sorted(eligible), sample_size)

    out_path = config.DATA_DIR / OUT_NAME
    queries = 0
    total_relevant = 0
    with open(out_path, "w", encoding="utf-8") as handle:
        for doc_id in sampled:
            entry = eligible[doc_id]
            for template in QUERY_TEMPLATES:
                record = {
                    "query": template.format(entry["title"]),
                    "doc_id": doc_id,
                    "title": entry["title"],
                    "relevant_ids": entry["ids"],
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                queries += 1
                total_relevant += len(entry["ids"])

    mean_relevant = total_relevant / queries if queries else 0.0
    print(
        f"docs sampled: {sample_size} | queries written: {queries} | "
        f"mean relevant-set size: {mean_relevant:.2f} -> {out_path}"
    )


if __name__ == "__main__":
    main()
