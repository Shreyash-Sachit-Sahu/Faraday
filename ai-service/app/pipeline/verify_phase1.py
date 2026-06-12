"""Phase 1 verification: one PASS/FAIL line per check, nonzero exit on any FAIL."""

import argparse
import sys
from typing import Callable

from app import config

CHUNK_FILES = ["chunks_wikipedia.jsonl", "chunks_mmlu.jsonl", "chunks_codealpaca.jsonl"]
DENSE_QUERY = "How does quicksort partition the array?"
BM25_QUERY = "TCP three way handshake"


def jsonl_line_counts() -> dict[str, int | None]:
    """Non-empty line count per expected chunk file; None if a file is missing."""
    counts: dict[str, int | None] = {}
    for name in CHUNK_FILES:
        path = config.DATA_DIR / name
        if not path.exists():
            counts[name] = None
            continue
        with open(path, "r", encoding="utf-8") as handle:
            counts[name] = sum(1 for line in handle if line.strip())
    return counts


def check_cuda() -> tuple[bool, str]:
    import torch  # lazy: heavy dependency

    available = torch.cuda.is_available()
    device = torch.cuda.get_device_name(0) if available else "no CUDA device"
    return available, f"torch.cuda.is_available()={available} ({device})"


def check_chunk_files() -> tuple[bool, str]:
    counts = jsonl_line_counts()
    ok = all(count for count in counts.values())
    detail = ", ".join(
        f"{name}={'MISSING' if count is None else count}"
        for name, count in counts.items()
    )
    return ok, detail


def check_qdrant_count() -> tuple[bool, str]:
    from qdrant_client import QdrantClient  # lazy: heavy dependency

    expected = sum(count or 0 for count in jsonl_line_counts().values())
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=30)
    stored = client.count(config.QDRANT_COLLECTION).count
    return stored == expected, f"qdrant count={stored}, jsonl lines={expected}"


def check_dense_search() -> tuple[bool, str]:
    import torch  # lazy: heavy dependency
    from qdrant_client import QdrantClient  # lazy: heavy dependency
    from sentence_transformers import SentenceTransformer  # lazy: heavy dependency

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(config.EMBED_MODEL, device=device)
    vector = model.encode(DENSE_QUERY, normalize_embeddings=True).tolist()
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=30)
    points = client.query_points(config.QDRANT_COLLECTION, query=vector, limit=5).points
    titles = [point.payload.get("title", "?") for point in points]
    sources = [point.payload.get("source", "?") for point in points]
    wiki_or_code = sum(1 for source in sources if source in {"wikipedia", "codealpaca"})
    ok = len(points) == 5 and wiki_or_code >= 3
    return ok, f"titles={titles}, sources={sources}, wiki/code hits={wiki_or_code}"


def check_bm25() -> tuple[bool, str]:
    import pickle

    import numpy as np

    from app.pipeline.stage5_bm25 import tokenize

    with open(config.DATA_DIR / "bm25_index.pkl", "rb") as handle:
        index = pickle.load(handle)
    scores = index["bm25"].get_scores(tokenize(BM25_QUERY))
    top5 = [index["titles"][int(i)] for i in np.argsort(scores)[::-1][:5]]
    return len(top5) == 5, f"top5={top5}"


def main() -> None:
    argparse.ArgumentParser(description="Verify Phase 1 artifacts.").parse_args()
    checks: list[tuple[str, Callable[[], tuple[bool, str]]]] = [
        ("cuda available", check_cuda),
        ("chunk files present", check_chunk_files),
        ("qdrant count matches jsonl", check_qdrant_count),
        ("dense search smoke", check_dense_search),
        ("bm25 smoke", check_bm25),
    ]
    failed = False
    for name, func in checks:
        try:
            ok, detail = func()
        except Exception as exc:  # noqa: BLE001 — a crashing check is a FAIL, not a crash
            ok, detail = False, f"raised: {exc}"
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        failed = failed or not ok
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
