"""Query-time graph-hop retrieval: query entities -> chunks, plus one hop."""

from app import config
from app.graph.entities import get_ner_model, keep_entity, normalize_entity, ENTITY_LABELS
from app.graph.neo4j_client import get_neo4j_driver

DIRECT_CYPHER = """
MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
WHERE e.name IN $names AND c.owner_id IN $owner_ids
WITH c.id AS chunk_id, count(DISTINCT e) AS hits
RETURN chunk_id, hits
ORDER BY hits DESC
LIMIT $limit
"""

NEIGHBOR_CYPHER = """
MATCH (e:Entity)-[r:CO_OCCURS]-(:Entity)<-[:MENTIONS]-(c:Chunk)
WHERE e.name IN $names AND c.owner_id IN $owner_ids
WITH c.id AS chunk_id, sum(r.count) AS strength
RETURN chunk_id, strength
ORDER BY strength DESC
LIMIT $limit
"""


def extract_query_entities(query: str) -> list[str]:
    model = get_ner_model()  # CPU by default — protects the GPU invariant
    preds = model.predict_entities(
        query[:1500], ENTITY_LABELS, threshold=config.GRAPH_NER_THRESHOLD
    )
    names = {normalize_entity(p["text"]) for p in preds}
    return [n for n in names if keep_entity(n)]


def graph_search(
    query: str, k: int = 50, owner_ids: list[str] | None = None
) -> list[tuple[str, float]]:
    owner_ids = owner_ids or ["global"]
    names = extract_query_entities(query)
    if not names:
        return []
    driver = get_neo4j_driver()
    scores: dict[str, float] = {}
    with driver.session() as session:
        for rec in session.run(
            DIRECT_CYPHER, names=names, owner_ids=owner_ids, limit=k
        ):
            scores[rec["chunk_id"]] = scores.get(rec["chunk_id"], 0.0) + 2.0 * rec["hits"]
        for rec in session.run(
            NEIGHBOR_CYPHER, names=names, owner_ids=owner_ids, limit=k * 2
        ):
            scores[rec["chunk_id"]] = (
                scores.get(rec["chunk_id"], 0.0) + 0.1 * float(rec["strength"])
            )
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "How does TCP relate to IP?"
    print("query entities:", extract_query_entities(q))
    for cid, score in graph_search(q, k=10):
        print(f"{score:7.3f}  {cid}")
