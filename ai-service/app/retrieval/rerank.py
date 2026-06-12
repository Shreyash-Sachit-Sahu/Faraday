"""Cross-encoder reranking of candidate chunks."""

from typing import Any

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_MODEL: Any = None


def _get_model() -> Any:
    """Lazy singleton for the cross-encoder."""
    global _MODEL
    if _MODEL is None:
        import torch  # lazy: heavy dependency
        from sentence_transformers import CrossEncoder  # lazy: heavy dependency

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = CrossEncoder(RERANK_MODEL, device=device)
    return _MODEL


def rerank(
    query: str, candidates: list[tuple[str, str]], top_k: int = 8
) -> list[tuple[str, float]]:
    """Re-score (chunk_id, text) candidates against the query, best first."""
    if not candidates:
        return []
    scores = _get_model().predict(
        [(query, text) for _, text in candidates], batch_size=32
    )
    ranked = sorted(
        (
            (chunk_id, float(score))
            for (chunk_id, _), score in zip(candidates, scores)
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[:top_k]


if __name__ == "__main__":
    demo_query = "How does TCP establish a connection?"
    demo_candidates = [
        ("doc-bread", "Bread dough must rest so the gluten can develop before baking."),
        ("doc-tcp", "TCP opens a connection with a three-way handshake of SYN, SYN-ACK and ACK."),
    ]
    for chunk_id, score in rerank(demo_query, demo_candidates, top_k=2):
        print(f"{score:8.3f}  {chunk_id}")
