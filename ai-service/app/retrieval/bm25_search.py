"""BM25 search over the pickled Phase 1 index."""

import pickle
from typing import Any

import numpy as np

from app import config
from app.pipeline.stage5_bm25 import tokenize

_INDEX: dict[str, Any] | None = None


def _get_index() -> dict[str, Any]:
    """Lazy singleton for the pickled BM25 index dict (ids, titles, bm25)."""
    global _INDEX
    if _INDEX is None:
        with open(config.DATA_DIR / "bm25_index.pkl", "rb") as handle:
            _INDEX = pickle.load(handle)
    return _INDEX


def bm25_search(query: str, k: int = 50) -> list[tuple[str, float]]:
    """Top-k (chunk_id, bm25_score) pairs for the query, best first."""
    index = _get_index()
    scores = index["bm25"].get_scores(tokenize(query))
    top = np.argsort(scores)[::-1][:k]
    return [(index["ids"][int(i)], float(scores[int(i)])) for i in top]


if __name__ == "__main__":
    index = _get_index()
    titles = dict(zip(index["ids"], index["titles"]))
    for chunk_id, score in bm25_search("TCP three way handshake", k=5):
        print(f"{score:8.3f}  {chunk_id}  {titles[chunk_id]}")
