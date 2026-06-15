"""Per-user document ingestion and deletion."""

import asyncio
import io

from fastapi import APIRouter, File, Form, UploadFile

from app import config
from app.api.retrieval_routes import GPU_EXECUTOR, CPU_EXECUTOR
from app.graph.entities import ENTITY_LABELS, get_ner_model, keep_entity, normalize_entity
from app.graph.neo4j_client import get_neo4j_driver
from app.pipeline.chunking import chunk_text
from app.pipeline.schema import Chunk
from app.retrieval.dense_search import get_embedder, get_qdrant_client

router = APIRouter()


def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith(".docx"):
        import docx

        document = docx.Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in document.paragraphs)
    return data.decode("utf-8", errors="ignore")  # .txt / .md / other text


UPSERT_BATCH = 256
UPLOAD_MENTIONS_CYPHER = """
UNWIND $batch AS row
MERGE (c:Chunk {id: row.chunk_id})
  SET c.owner_id = row.owner_id, c.source = 'upload', c.doc_id = row.doc_id
WITH c, row
UNWIND row.entities AS ent
  MERGE (e:Entity {name: ent.name})
    ON CREATE SET e.display = ent.display
  MERGE (c)-[:MENTIONS]->(e)
"""


def _embed_and_upsert(chunks: list[Chunk]) -> None:
    from qdrant_client.models import PointStruct

    model = get_embedder()
    vectors = model.encode(
        [c.text for c in chunks], batch_size=64, normalize_embeddings=True
    )
    client = get_qdrant_client()
    points = [
        PointStruct(id=c.id, vector=vectors[i].tolist(), payload=c.__dict__)
        for i, c in enumerate(chunks)
    ]
    for i in range(0, len(points), UPSERT_BATCH):
        client.upsert(config.QDRANT_COLLECTION, points=points[i : i + UPSERT_BATCH])


def _add_to_graph(chunks: list[Chunk]) -> None:
    model = get_ner_model()  # CPU per config
    rows = []
    for c in chunks:
        best: dict[str, dict] = {}
        for e in model.predict_entities(
            c.text[:1500], ENTITY_LABELS, threshold=config.GRAPH_NER_THRESHOLD
        ):
            name = normalize_entity(e["text"])
            if keep_entity(name) and (name not in best or e["score"] > best[name]["score"]):
                # store score too: the dedup compares best[name]["score"] on repeats
                # (the Cypher only reads name/display, so the extra field is harmless)
                best[name] = {"name": name, "display": e["text"].strip(), "score": e["score"]}
        rows.append(
            {"chunk_id": c.id, "owner_id": c.owner_id, "doc_id": c.doc_id,
             "entities": list(best.values())}
        )
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(UPLOAD_MENTIONS_CYPHER, batch=rows)


def ingest_document(owner_id: str, doc_id: str, filename: str, data: bytes) -> int:
    text = extract_text(filename, data)
    pieces = chunk_text(filename, text)
    if not pieces:
        return 0
    chunks = [
        Chunk(
            id=Chunk.make_id("upload", doc_id, i),
            text=piece, source="upload", title=filename,
            doc_id=doc_id, chunk_index=i, url="",
            owner_id=owner_id, doc_kind="upload",
        )
        for i, piece in enumerate(pieces)
    ]
    _embed_and_upsert(chunks)
    _add_to_graph(chunks)
    return len(chunks)


def _delete_document(owner_id: str, doc_id: str) -> None:
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_qdrant_client()
    flt = Filter(must=[
        FieldCondition(key="owner_id", match=MatchValue(value=owner_id)),
        FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
    ])
    client.delete(config.QDRANT_COLLECTION, points_selector=flt)
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(
            "MATCH (c:Chunk {owner_id: $o, doc_id: $d}) DETACH DELETE c",
            o=owner_id, d=doc_id,
        )


@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    owner_id: str = Form(...),
    doc_id: str = Form(...),
) -> dict:
    data = await file.read()
    loop = asyncio.get_running_loop()
    count = await loop.run_in_executor(
        GPU_EXECUTOR, ingest_document, owner_id, doc_id, file.filename, data
    )
    return {"chunk_count": count}


@router.delete("/documents")
async def delete_document(owner_id: str, doc_id: str) -> dict:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(CPU_EXECUTOR, _delete_document, owner_id, doc_id)
    return {"deleted": True}
