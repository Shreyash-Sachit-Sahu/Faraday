"""Step D: load chunk_entities.jsonl into Neo4j as chunk/entity/co-occurrence graph."""

import argparse
import json
from collections import Counter
from itertools import combinations

from app import config
from app.graph.neo4j_client import ensure_schema, get_neo4j_driver

IN_NAME = "chunk_entities.jsonl"


def compute_cooccurrence(
    per_chunk_entities: list[list[str]],
    min_count: int,
    freq_floor: int = 2,
) -> list[tuple[str, str, int]]:
    """Undirected co-occurrence counts, filtered.

    freq_floor drops entities too rare to ever form a frequent pair, which
    shrinks the pair space dramatically before counting. Dedupe per chunk so
    repeated mentions count once. Sorted pair keys make (a,b) deterministic.
    """
    freq: Counter = Counter()
    for ents in per_chunk_entities:
        freq.update(set(ents))

    pair_counts: Counter = Counter()
    for ents in per_chunk_entities:
        kept = sorted({e for e in ents if freq[e] >= freq_floor})
        for a, b in combinations(kept, 2):
            pair_counts[(a, b)] += 1

    return [(a, b, c) for (a, b), c in pair_counts.items() if c >= min_count]


MENTIONS_CYPHER = """
UNWIND $batch AS row
MERGE (c:Chunk {id: row.chunk_id})
  SET c.owner_id = row.owner_id, c.source = row.source
WITH c, row
UNWIND row.entities AS ent
  MERGE (e:Entity {name: ent.name})
    ON CREATE SET e.display = ent.display
  MERGE (c)-[:MENTIONS]->(e)
"""

COOCCUR_CYPHER = """
UNWIND $batch AS row
MATCH (a:Entity {name: row.a})
MATCH (b:Entity {name: row.b})
MERGE (a)-[r:CO_OCCURS]-(b)
  SET r.count = row.count
"""


def run_batched(driver, cypher, rows, batch_size):
    from tqdm import tqdm

    with driver.session() as session:
        for i in tqdm(range(0, len(rows), batch_size)):
            session.run(cypher, batch=rows[i : i + batch_size])


def wipe_graph(driver) -> None:
    """Batched delete so the 1 GB heap never deletes everything at once."""
    with driver.session() as session:
        while True:
            result = session.run(
                "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(n) AS c"
            )
            if result.single()["c"] == 0:
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Neo4j graph.")
    parser.add_argument("--min-cooccur", type=int, default=3)
    parser.add_argument("--max-entities-per-chunk", type=int, default=15)
    parser.add_argument("--wipe", action="store_true")
    args = parser.parse_args()

    driver = get_neo4j_driver()
    if args.wipe:
        print("wiping graph...")
        wipe_graph(driver)
    ensure_schema()

    in_path = config.DATA_DIR / IN_NAME
    mention_rows: list[dict] = []
    per_chunk_entities: list[list[str]] = []
    with open(in_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ents = row["entities"]
            if not ents:
                continue
            capped = sorted(ents, key=lambda e: e["score"], reverse=True)[
                : args.max_entities_per_chunk
            ]
            mention_rows.append(
                {
                    "chunk_id": row["chunk_id"],
                    "owner_id": row.get("owner_id", "global"),
                    "source": row.get("source", ""),
                    "entities": [
                        {"name": e["name"], "display": e["display"]} for e in capped
                    ],
                }
            )
            per_chunk_entities.append([e["name"] for e in capped])

    print(f"chunks with entities: {len(mention_rows)} -> writing MENTIONS")
    run_batched(driver, MENTIONS_CYPHER, mention_rows, 2000)

    print("computing co-occurrence...")
    pairs = compute_cooccurrence(per_chunk_entities, min_count=args.min_cooccur)
    cooccur_rows = [{"a": a, "b": b, "count": c} for (a, b, c) in pairs]
    print(f"co-occurrence pairs (count >= {args.min_cooccur}): {len(cooccur_rows)}")
    run_batched(driver, COOCCUR_CYPHER, cooccur_rows, 5000)

    n_chunk = len(mention_rows)
    n_entity = len({name for ents in per_chunk_entities for name in ents})
    n_mentions = sum(len(ents) for ents in per_chunk_entities)
    n_cooccurs = len(cooccur_rows)
    print(
        f"written -> #Chunk={n_chunk} #Entity={n_entity} "
        f"#MENTIONS={n_mentions} #CO_OCCURS={n_cooccurs}"
    )


if __name__ == "__main__":
    main()
