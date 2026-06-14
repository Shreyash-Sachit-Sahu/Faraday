"""Async retrieval endpoint with caching, backpressure, and stage timings."""

import asyncio
import statistics
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from cachetools import TTLCache
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import config
from app.graph.graph_search import graph_search
from app.retrieval.bm25_search import bm25_search
from app.retrieval.dense_search import dense_search, get_qdrant_client
from app.retrieval.fusion import rrf_fuse
from app.retrieval.rerank import rerank

router = APIRouter()


async def _timed_leg(future):
    """Await a retrieval-leg future and return (result, elapsed_ms)."""
    start = time.perf_counter()
    result = await future
    return result, (time.perf_counter() - start) * 1000

# ONE thread for all GPU work (embed + rerank share 4 GB VRAM — never parallel).
GPU_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gpu")
# Small pool for CPU/network work (BM25 scoring, Qdrant payload fetch).
CPU_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cpu")

SEM = asyncio.Semaphore(config.RETRIEVAL_CONCURRENCY)
CACHE: TTLCache = TTLCache(maxsize=2048, ttl=config.RETRIEVAL_CACHE_TTL)

LATENCIES: deque = deque(maxlen=1000)
COUNTERS = {"requests": 0, "cache_hits": 0, "errors": 0, "rejected": 0}


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=8, ge=1, le=20)
    owner_ids: list[str] = Field(default=["global"], max_length=2)


def _retrieve_sync_parts(query: str, k: int, owner_ids: list[str]) -> dict:
    raise NotImplementedError("not used — stages run individually below")


@router.post("/retrieve")
async def retrieve_endpoint(req: RetrieveRequest) -> dict:
    COUNTERS["requests"] += 1
    cache_key = (req.query.strip().lower(), req.k, tuple(sorted(req.owner_ids)))
    if cache_key in CACHE:
        COUNTERS["cache_hits"] += 1
        return {**CACHE[cache_key], "cached": True}

    try:
        await asyncio.wait_for(
            SEM.acquire(), timeout=config.RETRIEVAL_QUEUE_TIMEOUT
        )
    except asyncio.TimeoutError:
        COUNTERS["rejected"] += 1
        raise HTTPException(
            status_code=503,
            detail="Retrieval saturated, retry shortly.",
            headers={"Retry-After": "2"},
        )

    loop = asyncio.get_running_loop()
    t0 = time.perf_counter()
    try:
        # BM25 (CPU), dense (GPU+network), and graph (CPU NER + Neo4j) legs in
        # parallel. graph stays on CPU_EXECUTOR so it never contends for the GPU.
        bm25_task = loop.run_in_executor(
            CPU_EXECUTOR, bm25_search, req.query, 50
        )
        dense_task = loop.run_in_executor(
            GPU_EXECUTOR, dense_search, req.query, 50, req.owner_ids
        )
        graph_task = (
            loop.run_in_executor(CPU_EXECUTOR, graph_search, req.query, 50, req.owner_ids)
            if config.RETRIEVAL_USE_GRAPH
            else None
        )
        legs = [_timed_leg(bm25_task), _timed_leg(dense_task)]
        if graph_task is not None:
            legs.append(_timed_leg(graph_task))
        gathered = await asyncio.gather(*legs)
        bm25_hits = gathered[0][0]
        dense_hits = gathered[1][0]
        if graph_task is not None:
            graph_hits, graph_ms = gathered[2][0], round(gathered[2][1], 1)
        else:
            graph_hits, graph_ms = [], 0.0
        t1 = time.perf_counter()

        rankings = [[i for i, _ in bm25_hits], [i for i, _ in dense_hits]]
        if graph_task is not None:
            rankings.append([i for i, _ in graph_hits])
        fused = rrf_fuse(rankings)
        top_ids = [doc_id for doc_id, _ in fused[: config.RETRIEVAL_RERANK_IN]]
        t2 = time.perf_counter()

        points = await loop.run_in_executor(
            CPU_EXECUTOR,
            lambda: get_qdrant_client().retrieve(
                config.QDRANT_COLLECTION, ids=top_ids, with_payload=True
            ),
        )
        payloads = {str(p.id): p.payload for p in points}
        candidates = [
            (i, payloads[i]["text"]) for i in top_ids if i in payloads
        ]
        t3 = time.perf_counter()

        reranked = await loop.run_in_executor(
            GPU_EXECUTOR, rerank, req.query, candidates, req.k
        )
        t4 = time.perf_counter()

        results = []
        for doc_id, score in reranked:
            p = payloads[doc_id]
            results.append(
                {
                    "id": doc_id,
                    "score": round(float(score), 4),
                    "title": p.get("title", ""),
                    "source": p.get("source", ""),
                    "url": p.get("url", ""),
                    "text": p.get("text", ""),
                }
            )
        response = {
            "results": results,
            "timings_ms": {
                "legs": round((t1 - t0) * 1000, 1),
                "graph": graph_ms,
                "fuse": round((t2 - t1) * 1000, 1),
                "fetch": round((t3 - t2) * 1000, 1),
                "rerank": round((t4 - t3) * 1000, 1),
                "total": round((t4 - t0) * 1000, 1),
            },
            "cached": False,
        }
        CACHE[cache_key] = {k_: v for k_, v in response.items() if k_ != "cached"}
        LATENCIES.append((t4 - t0) * 1000)
        return response
    except HTTPException:
        raise
    except Exception:
        COUNTERS["errors"] += 1
        raise HTTPException(status_code=500, detail="retrieval failed")
    finally:
        SEM.release()


@router.get("/metrics")
async def metrics() -> dict:
    lat = sorted(LATENCIES)
    return {
        **COUNTERS,
        "window": len(lat),
        "p50_ms": round(statistics.median(lat), 1) if lat else None,
        "p95_ms": round(lat[int(0.95 * (len(lat) - 1))], 1) if lat else None,
    }
