import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import config
from app.api.retrieval_routes import GPU_EXECUTOR, CPU_EXECUTOR, router
from app.api.chat_routes import router as chat_router
from app.api.ingest_routes import router as ingest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    from app.graph.graph_search import extract_query_entities
    from app.retrieval.bm25_search import bm25_search
    from app.retrieval.dense_search import dense_search
    from app.retrieval.rerank import rerank

    loop = asyncio.get_running_loop()
    warmups = [
        ("bm25", CPU_EXECUTOR, lambda: bm25_search("warmup query", 1)),
        ("dense", GPU_EXECUTOR, lambda: dense_search("warmup query", 1)),
        ("rerank", GPU_EXECUTOR, lambda: rerank("warmup", [("w", "warm text")], 1)),
    ]
    if config.RETRIEVAL_USE_GRAPH:
        warmups.append(
            ("graph", CPU_EXECUTOR, lambda: extract_query_entities("warmup"))
        )
    warmups.append(
        ("generator", GPU_EXECUTOR, lambda: __import__(
            "app.inference.generator", fromlist=["_load"]
        )._load()),
    )
    for name, executor, fn in warmups:
        t0 = time.perf_counter()
        await loop.run_in_executor(executor, fn)
        print(f"[warmup] {name} ready in {time.perf_counter() - t0:.1f}s")
    yield
    GPU_EXECUTOR.shutdown(wait=False)
    CPU_EXECUTOR.shutdown(wait=False)


app = FastAPI(title="Faraday AI service", lifespan=lifespan)
app.include_router(router)
app.include_router(chat_router)
app.include_router(ingest_router)


@app.get("/health")
def health() -> dict:
    status: dict = {"service": "ok", "qdrant": "unknown", "neo4j": "unknown"}

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=3
        )
        client.get_collections()
        status["qdrant"] = "ok"
    except Exception as exc:
        status["qdrant"] = f"error: {exc}"

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        driver.close()
        status["neo4j"] = "ok"
    except Exception as exc:
        status["neo4j"] = f"error: {exc}"

    return status
