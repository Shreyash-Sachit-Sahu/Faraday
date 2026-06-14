"""Step H.4: relational probes — same query with the graph leg on vs off.

Shows what the graph leg surfaces even when the aggregate factoid metric is
flat, by printing top-5 titles for each side of four relational questions.
"""

import argparse

from app.retrieval.retriever import retrieve

PROBES = [
    "How are hash tables related to hash functions?",
    "What algorithms are used in public key cryptography?",
    "How does TCP relate to IP in the protocol stack?",
    "What data structures does Dijkstra's algorithm use?",
]
TOP_K = 5


def _titles(query: str, use_graph: bool) -> list[str]:
    return [
        f"[{c.source}] {c.title}"
        for c in retrieve(query, k_final=TOP_K, use_graph=use_graph)
    ]


def main() -> None:
    argparse.ArgumentParser(description="Run the graph relational probes.").parse_args()
    for query in PROBES:
        print(f"\n=== {query} ===")
        no_graph = _titles(query, use_graph=False)
        with_graph = _titles(query, use_graph=True)
        print("  --no-graph:")
        for title in no_graph:
            print(f"    - {title}")
        print("  --graph:")
        for title in with_graph:
            print(f"    - {title}")


if __name__ == "__main__":
    main()
