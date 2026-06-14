"""Single retrieval entry point: BM25 + dense -> RRF -> cross-encoder rerank."""

import argparse
from dataclasses import dataclass

from app import config
from app.graph.graph_search import graph_search
from app.retrieval.bm25_search import bm25_search
from app.retrieval.dense_search import dense_search, get_client
from app.retrieval.fusion import rrf_fuse
from app.retrieval.rerank import rerank


@dataclass
class RetrievedChunk:
    id: str
    text: str
    title: str
    source: str
    url: str
    score: float


def retrieve(
    query: str,
    k_final: int = 8,
    k_bm25: int = 50,
    k_dense: int = 50,
    k_rerank_in: int = 40,
    owner_ids: list[str] | None = None,
    use_graph: bool | None = None,
) -> list[RetrievedChunk]:
    """Fused and reranked top chunks for the query, best first.

    With use_graph on, a third (relational) leg from the Neo4j graph joins the
    same unweighted rrf_fuse. Off (default falls back to config) is byte-
    identical to the Phase 2 two-leg pipeline.
    """
    if use_graph is None:
        use_graph = config.RETRIEVAL_USE_GRAPH
    bm25_ids = [chunk_id for chunk_id, _ in bm25_search(query, k_bm25)]
    dense_ids = [chunk_id for chunk_id, _ in dense_search(query, k_dense, owner_ids)]
    rankings = [bm25_ids, dense_ids]
    if use_graph:
        graph_ids = [chunk_id for chunk_id, _ in graph_search(query, k_dense, owner_ids)]
        rankings.append(graph_ids)
    fused = rrf_fuse(rankings)
    top_ids = [doc_id for doc_id, _ in fused[:k_rerank_in]]

    records = get_client().retrieve(
        config.QDRANT_COLLECTION, ids=top_ids, with_payload=True
    )
    payloads = {str(record.id): record.payload for record in records}
    candidates = [
        (chunk_id, payloads[chunk_id]["text"])
        for chunk_id in top_ids
        if chunk_id in payloads
    ]
    ranked = rerank(query, candidates, top_k=k_final)

    chunks: list[RetrievedChunk] = []
    for chunk_id, score in ranked:
        payload = payloads[chunk_id]
        chunks.append(
            RetrievedChunk(
                id=chunk_id,
                text=payload.get("text", ""),
                title=payload.get("title", ""),
                source=payload.get("source", ""),
                url=payload.get("url", ""),
                score=score,
            )
        )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid retrieval CLI.")
    parser.add_argument("query", type=str, help="question to retrieve for")
    parser.add_argument(
        "--graph",
        dest="use_graph",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="force the graph leg on (--graph) or off (--no-graph); default: config",
    )
    args = parser.parse_args()
    for rank, chunk in enumerate(
        retrieve(args.query, use_graph=args.use_graph), start=1
    ):
        snippet = chunk.text[:150].replace("\n", " ")
        print(f"{rank:2d}. {chunk.score:7.3f}  [{chunk.source}] {chunk.title}")
        print(f"    {snippet}")


if __name__ == "__main__":
    main()
