"""Stage 3: turn CodeAlpaca task/solution pairs into single-chunk documents."""

import argparse

from app import config
from app.pipeline.schema import Chunk

OUT_NAME = "chunks_codealpaca.jsonl"
MIN_TEXT_CHARS = 80
MAX_TEXT_CHARS = 4000
TITLE_CHARS = 60


def build_title(prompt: str) -> str:
    """First 60 chars of the prompt collapsed to a single line."""
    return " ".join(prompt.split())[:TITLE_CHARS]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write CodeAlpaca pairs as chunk JSONL.")
    parser.add_argument("--limit", type=int, default=0, help="max items (0 = all)")
    args = parser.parse_args()

    from datasets import load_dataset  # lazy: heavy dependency

    rows = load_dataset("HuggingFaceH4/CodeAlpaca_20K", split="train")

    out_path = config.DATA_DIR / OUT_NAME
    written = skipped = 0
    with open(out_path, "w", encoding="utf-8") as handle:
        for index, row in enumerate(rows):
            if args.limit and written >= args.limit:
                break
            text = f"Task: {row['prompt']}\n\nSolution:\n{row['completion']}"
            if len(text) < MIN_TEXT_CHARS:
                skipped += 1
                continue
            doc_id = f"codealpaca-{index}"
            chunk = Chunk(
                id=Chunk.make_id("codealpaca", doc_id, 0),
                text=text[:MAX_TEXT_CHARS],
                source="codealpaca",
                title=build_title(row["prompt"]),
                doc_id=doc_id,
                chunk_index=0,
            )
            handle.write(chunk.to_json() + "\n")
            written += 1
    print(f"chunks written: {written} | skipped short: {skipped} -> {out_path}")


if __name__ == "__main__":
    main()
