"""Step E: verify the Neo4j graph — PASS/FAIL lines, nonzero exit on hard failure."""

import argparse
import sys

from app import config
from app.graph.graph_search import graph_search
from app.graph.neo4j_client import get_neo4j_driver

SPOT_CANDIDATES = ["tcp", "quicksort"]
GRAPH_QUERY = "How does TCP relate to IP?"


def _scalar(session, cypher: str):
    return session.run(cypher).single()[0]


def main() -> None:
    argparse.ArgumentParser(description="Verify the Phase 3 graph.").parse_args()
    driver = get_neo4j_driver()
    failed = False

    with driver.session() as session:
        n_chunk = _scalar(session, "MATCH (c:Chunk) RETURN count(c)")
        n_entity = _scalar(session, "MATCH (e:Entity) RETURN count(e)")
        n_mentions = _scalar(session, "MATCH ()-[m:MENTIONS]->() RETURN count(m)")
        n_cooccurs = _scalar(session, "MATCH ()-[r:CO_OCCURS]->() RETURN count(r)")

        ok1 = all(v > 0 for v in (n_chunk, n_entity, n_mentions, n_cooccurs))
        failed = failed or not ok1
        print(
            f"[{'PASS' if ok1 else 'FAIL'}] counts: #Chunk={n_chunk} "
            f"#Entity={n_entity} #MENTIONS={n_mentions} #CO_OCCURS={n_cooccurs}"
        )

        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=30
        )
        qdrant_count = client.count(config.QDRANT_COLLECTION).count
        ratio = n_chunk / qdrant_count if qdrant_count else 0.0
        ok2 = 0.0 < ratio <= 1.0
        failed = failed or not ok2
        in_band = "in" if 0.6 <= ratio <= 0.95 else "OUT OF"
        print(
            f"[{'PASS' if ok2 else 'FAIL'}] coverage: {n_chunk}/{qdrant_count} = "
            f"{ratio:.4f} ({in_band} expected 0.6-0.95 band)"
        )

        top = session.run(
            "MATCH (e:Entity)<-[m:MENTIONS]-() "
            "RETURN e.display AS d, count(m) AS deg ORDER BY deg DESC LIMIT 10"
        ).data()
        ok3 = len(top) > 0
        failed = failed or not ok3
        print(f"[{'PASS' if ok3 else 'FAIL'}] top-10 entities by MENTIONS degree:")
        for row in top:
            print(f"        {row['deg']:7d}  {row['d']}")

        chosen = None
        neighbors: list = []
        for name in SPOT_CANDIDATES:
            rows = session.run(
                "MATCH (e:Entity {name:$name})-[r:CO_OCCURS]-(n:Entity) "
                "RETURN n.display AS d, r.count AS c ORDER BY c DESC LIMIT 10",
                name=name,
            ).data()
            if rows:
                chosen, neighbors = name, rows
                break
        if chosen is None:
            fallback = session.run(
                "MATCH (e:Entity)-[r:CO_OCCURS]-(n:Entity) "
                "RETURN e.name AS src, n.display AS d, r.count AS c "
                "ORDER BY c DESC LIMIT 10"
            ).data()
            chosen = fallback[0]["src"] if fallback else "(none)"
            neighbors = fallback
        ok4 = len(neighbors) > 0
        failed = failed or not ok4
        print(f"[{'PASS' if ok4 else 'FAIL'}] CO_OCCURS neighbors of '{chosen}':")
        for row in neighbors:
            print(f"        {row['c']:7d}  {row['d']}")

    hits = graph_search(GRAPH_QUERY)
    ok5 = len(hits) >= 1
    failed = failed or not ok5
    print(
        f"[{'PASS' if ok5 else 'FAIL'}] graph_search({GRAPH_QUERY!r}) "
        f"returned {len(hits)} chunk ids"
    )

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
