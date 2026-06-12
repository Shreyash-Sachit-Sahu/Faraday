from fastapi import FastAPI

from app import config

app = FastAPI(title="Faraday AI service")


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
