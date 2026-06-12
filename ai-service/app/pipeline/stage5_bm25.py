"""Stage 5: build a BM25 index over all chunks and pickle it to disk."""

import argparse
import pickle
import re

from app import config
from app.pipeline.io_utils import load_all_chunks

OUT_NAME = "bm25_index.pkl"
SAMPLE_QUERY = "binary search tree complexity"


def tokenize(text: str) -> list[str]:
    """Lowercase tokens that keep c++, c#, python3 and snake_case searchable."""
    return re.findall(r"[a-z0-9_+#]+", text.lower())


def main() -> None:
    argparse.ArgumentParser(
        description="Build the BM25 pickle from chunk JSONLs."
    ).parse_args()

    chunks = load_all_chunks(config.DATA_DIR)
    if not chunks:
        raise SystemExit(f"no chunks_*.jsonl content found in {config.DATA_DIR}")

    import numpy as np
    from rank_bm25 import BM25Okapi  # lazy: heavy dependency

    token_lists = [tokenize(chunk.text) for chunk in chunks]
    bm25 = BM25Okapi(token_lists)

    out_path = config.DATA_DIR / OUT_NAME
    payload = {
        "ids": [chunk.id for chunk in chunks],
        "titles": [chunk.title for chunk in chunks],
        "bm25": bm25,
    }
    with open(out_path, "wb") as handle:
        pickle.dump(payload, handle)

    size_mb = out_path.stat().st_size / (1024 * 1024)
    scores = bm25.get_scores(tokenize(SAMPLE_QUERY))
    top5 = [payload["titles"][int(i)] for i in np.argsort(scores)[::-1][:5]]
    print(f"corpus size: {len(chunks)} | pickle size: {size_mb:.1f} MB -> {out_path}")
    print(f"top-5 titles for {SAMPLE_QUERY!r}: {top5}")


if __name__ == "__main__":
    main()
