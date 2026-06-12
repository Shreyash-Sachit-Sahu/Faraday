"""Evaluate four retrieval configurations on evalset.jsonl."""

import argparse
import json
import time
from typing import Any

from tqdm import tqdm

from app import config
from app.eval.metrics import mrr_at_k, precision_at_k, recall_at_k
from app.retrieval.bm25_search import bm25_search
from app.retrieval.dense_search import get_client, get_model
from app.retrieval.fusion import rrf_fuse
from app.retrieval.retriever import retrieve

K_CANDIDATES = 50
K_TOP = 10
CONFIG_NAMES = ["bm25", "dense", "rrf", "rrf_rerank"]


def load_evalset() -> list[dict[str, Any]]:
    path = config.DATA_DIR / "evalset.jsonl"
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def batched_dense_search(queries: list[str], k: int) -> list[list[str]]:
    """Embed all queries in one encode call, then run the Qdrant queries."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    vectors = get_model().encode(
        queries, batch_size=64, normalize_embeddings=True, show_progress_bar=True
    )
    query_filter = Filter(
        must=[FieldCondition(key="owner_id", match=MatchAny(any=["global"]))]
    )
    client = get_client()
    results: list[list[str]] = []
    for vector in tqdm(vectors, desc="dense search", mininterval=5.0):
        points = client.query_points(
            config.QDRANT_COLLECTION,
            query=vector.tolist(),
            limit=k,
            query_filter=query_filter,
            with_payload=False,
        ).points
        results.append([str(point.id) for point in points])
    return results


def main() -> None:
    argparse.ArgumentParser(description="Run the Phase 2 retrieval eval.").parse_args()

    rows = load_evalset()
    queries = [row["query"] for row in rows]
    relevant_sets = [set(row["relevant_ids"]) for row in rows]
    print(f"queries: {len(rows)}")

    timings: dict[str, float] = {}

    start = time.perf_counter()
    bm25_lists = [
        [chunk_id for chunk_id, _ in bm25_search(query, K_CANDIDATES)]
        for query in tqdm(queries, desc="bm25 search", mininterval=5.0)
    ]
    timings["bm25"] = time.perf_counter() - start

    start = time.perf_counter()
    dense_lists = batched_dense_search(queries, K_CANDIDATES)
    timings["dense"] = time.perf_counter() - start

    start = time.perf_counter()
    rrf_lists = [
        [doc_id for doc_id, _ in rrf_fuse([bm25_ids, dense_ids])[:K_TOP]]
        for bm25_ids, dense_ids in zip(bm25_lists, dense_lists)
    ]
    timings["rrf"] = time.perf_counter() - start

    start = time.perf_counter()
    rerank_lists = [
        [chunk.id for chunk in retrieve(query, k_final=K_TOP)]
        for query in tqdm(queries, desc="rrf_rerank", mininterval=5.0)
    ]
    timings["rrf_rerank"] = time.perf_counter() - start

    ranked_by_config: dict[str, list[list[str]]] = {
        "bm25": [ids[:K_TOP] for ids in bm25_lists],
        "dense": [ids[:K_TOP] for ids in dense_lists],
        "rrf": rrf_lists,
        "rrf_rerank": rerank_lists,
    }

    results: dict[str, dict[str, float]] = {}
    for name in CONFIG_NAMES:
        ranked_lists = ranked_by_config[name]
        n = len(ranked_lists)
        results[name] = {
            "P@5": sum(
                precision_at_k(ranked, relevant, 5)
                for ranked, relevant in zip(ranked_lists, relevant_sets)
            )
            / n,
            "R@10": sum(
                recall_at_k(ranked, relevant, 10)
                for ranked, relevant in zip(ranked_lists, relevant_sets)
            )
            / n,
            "MRR@10": sum(
                mrr_at_k(ranked, relevant, 10)
                for ranked, relevant in zip(ranked_lists, relevant_sets)
            )
            / n,
        }

    print()
    print(f"{'config':<12}  {'P@5':<7}{'R@10':<8}{'MRR@10':<7}")
    for name in CONFIG_NAMES:
        row = results[name]
        print(
            f"{name:<12}  {row['P@5']:<7.3f}{row['R@10']:<8.3f}{row['MRR@10']:<7.3f}"
        )
    print()
    print(
        "timings (s): "
        + ", ".join(f"{name}={seconds:.1f}" for name, seconds in timings.items())
    )

    out_path = config.DATA_DIR / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({"n_queries": len(rows), "results": results}, handle, indent=2)
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
