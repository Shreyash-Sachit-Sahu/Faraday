"""Stage 1: stream English Wikipedia and keep CS-relevant articles as chunks."""

import argparse

from tqdm import tqdm

from app import config
from app.pipeline.chunking import chunk_text
from app.pipeline.schema import Chunk

CS_KEYWORDS = [
    "algorithm", "data structure", "computer science", "programming language",
    "software engineering", "operating system", "compiler", "interpreter",
    "database", "computer network", "machine learning", "artificial intelligence",
    "deep learning", "neural network", "cryptography", "computer security",
    "distributed system", "computational complexity", "computer architecture",
    "microprocessor", "graphics processing unit", "computer graphics",
    "information retrieval", "natural language processing", "computer vision",
    "source code", "version control", "concurrency", "parallel computing",
    "cloud computing", "web development", "internet protocol", "encryption",
    "boolean", "computability", "software",
    "network protocol", "communication protocol", "transmission control",
    "domain name system", "hypertext transfer", "ethernet", "routing",
    "firewall"
]

OUT_NAME = "chunks_wikipedia.jsonl"
HEAD_CHARS = 600
MIN_DISTINCT_HEAD_KEYWORDS = 2


def is_cs_article(title: str, text: str) -> bool:
    """Title contains any CS keyword, or first 600 chars contain >=2 distinct ones."""
    title_lower = title.lower()
    if any(keyword in title_lower for keyword in CS_KEYWORDS):
        return True
    head = text[:HEAD_CHARS].lower()
    distinct = sum(1 for keyword in CS_KEYWORDS if keyword in head)
    return distinct >= MIN_DISTINCT_HEAD_KEYWORDS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream Wikipedia, keep CS articles, write chunk JSONL."
    )
    parser.add_argument(
        "--max-articles", type=int, default=10000,
        help="stop after accepting this many articles",
    )
    parser.add_argument(
        "--max-scan", type=int, default=1500000,
        help="stop after scanning this many articles regardless",
    )
    args = parser.parse_args()

    from datasets import load_dataset  # lazy: heavy dependency

    dataset = load_dataset(
        "wikimedia/wikipedia", "20231101.en", split="train", streaming=True
    )

    out_path = config.DATA_DIR / OUT_NAME
    scanned = accepted = written = 0
    progress = tqdm(
        total=args.max_scan, desc="wikipedia scan", unit="article", mininterval=10.0
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        for record in dataset:
            scanned += 1
            progress.update(1)
            if is_cs_article(record["title"], record["text"]):
                accepted += 1
                for index, body in enumerate(chunk_text(record["title"], record["text"])):
                    chunk = Chunk(
                        id=Chunk.make_id("wikipedia", record["id"], index),
                        text=body,
                        source="wikipedia",
                        title=record["title"],
                        doc_id=record["id"],
                        chunk_index=index,
                        url=record["url"],
                    )
                    handle.write(chunk.to_json() + "\n")
                    written += 1
            if accepted >= args.max_articles or scanned >= args.max_scan:
                break
    progress.close()
    print(
        f"articles scanned: {scanned} | accepted: {accepted} | "
        f"chunks written: {written} -> {out_path}"
    )


if __name__ == "__main__":
    main()
