"""Dense search against Qdrant with the bge-small embedder."""

from typing import Any

from app import config

_MODEL: Any = None
_CLIENT: Any = None


def get_model() -> Any:
    """Lazy singleton for the sentence-transformer embedder."""
    global _MODEL
    if _MODEL is None:
        import torch  # lazy: heavy dependency
        from sentence_transformers import SentenceTransformer  # lazy: heavy dependency

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = SentenceTransformer(config.EMBED_MODEL, device=device)
    return _MODEL


def get_client() -> Any:
    """Lazy singleton for the Qdrant client (shared by retriever)."""
    global _CLIENT
    if _CLIENT is None:
        from qdrant_client import QdrantClient  # lazy: heavy dependency

        _CLIENT = QdrantClient(
            host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=30
        )
    return _CLIENT


def get_qdrant_client() -> Any:
    """Singleton Qdrant client, under the name the API layer imports (PHASE2_5.md)."""
    return get_client()


def get_embedder() -> Any:
    """The lazily-loaded SentenceTransformer singleton (shared with retrieval)."""
    return get_model()


def dense_search(
    query: str, k: int = 50, owner_ids: list[str] | None = None
) -> list[tuple[str, float]]:
    """Top-k (chunk_id, cosine_score) pairs, filtered to the given owner ids."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    if owner_ids is None:
        owner_ids = ["global"]
    vector = get_model().encode(query, normalize_embeddings=True).tolist()
    query_filter = Filter(
        must=[FieldCondition(key="owner_id", match=MatchAny(any=owner_ids))]
    )
    points = get_client().query_points(
        config.QDRANT_COLLECTION,
        query=vector,
        limit=k,
        query_filter=query_filter,
        with_payload=True,
    ).points
    return [(str(point.id), float(point.score)) for point in points]


if __name__ == "__main__":
    results = dense_search("How does quicksort partition the array?", k=5)
    records = get_client().retrieve(
        config.QDRANT_COLLECTION,
        ids=[chunk_id for chunk_id, _ in results],
        with_payload=True,
    )
    titles = {str(record.id): record.payload.get("title", "?") for record in records}
    for chunk_id, score in results:
        print(f"{score:.4f}  {chunk_id}  {titles.get(chunk_id, '?')}")
