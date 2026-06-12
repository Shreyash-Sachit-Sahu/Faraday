"""Stage 2: convert CS-adjacent MMLU configs into single-chunk Q&A documents."""

import argparse

from app import config
from app.pipeline.schema import Chunk

CONFIGS = [
    "college_computer_science",
    "high_school_computer_science",
    "computer_security",
    "machine_learning",
    "formal_logic",
]
SPLITS = ["test", "validation", "dev"]
OUT_NAME = "chunks_mmlu.jsonl"


def format_item(cfg: str, question: str, choices: list[str], answer: int) -> str:
    """Render one MMLU item as a self-contained Q&A text block."""
    options = "; ".join(f"{chr(65 + i)}) {choice}" for i, choice in enumerate(choices))
    return (
        f"{cfg.replace('_', ' ').title()} question: {question}\n"
        f"Options: {options}"
        f"\nCorrect answer: {chr(65 + answer)}) {choices[answer]}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Write MMLU CS items as chunk JSONL.")
    parser.add_argument(
        "--limit", type=int, default=0,
        help="max items per config as a running cap across splits (0 = no limit)",
    )
    args = parser.parse_args()

    from datasets import load_dataset  # lazy: heavy dependency

    out_path = config.DATA_DIR / OUT_NAME
    per_config: dict[str, int] = {}
    total = 0
    with open(out_path, "w", encoding="utf-8") as handle:
        for cfg in CONFIGS:
            count = 0
            for split in SPLITS:
                if args.limit and count >= args.limit:
                    break
                rows = load_dataset("cais/mmlu", cfg, split=split)
                for index, row in enumerate(rows):
                    if args.limit and count >= args.limit:
                        break
                    doc_id = f"{cfg}-{split}-{index}"
                    chunk = Chunk(
                        id=Chunk.make_id("mmlu", doc_id, 0),
                        text=format_item(
                            cfg, row["question"], list(row["choices"]), int(row["answer"])
                        ),
                        source="mmlu",
                        title=f"MMLU {cfg}",
                        doc_id=doc_id,
                        chunk_index=0,
                    )
                    handle.write(chunk.to_json() + "\n")
                    count += 1
            per_config[cfg] = count
            total += count
    summary = ", ".join(f"{cfg}={count}" for cfg, count in per_config.items())
    print(f"items per config: {summary}")
    print(f"total chunks written: {total} -> {out_path}")


if __name__ == "__main__":
    main()
