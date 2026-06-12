"""Standard retrieval metrics. retrieved: ranked ids, best first."""


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    hits = sum(1 for doc_id in retrieved[:k] if doc_id in relevant)
    return hits / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for doc_id in retrieved[:k] if doc_id in relevant)
    return hits / len(relevant)


def mrr_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    for i, doc_id in enumerate(retrieved[:k]):
        if doc_id in relevant:
            return 1.0 / (i + 1)
    return 0.0


if __name__ == "__main__":
    r = ["a", "b", "c", "d"]
    rel = {"b", "z"}
    print(precision_at_k(r, rel, 2), recall_at_k(r, rel, 4), mrr_at_k(r, rel, 4))
    # expected: 0.5 0.5 0.5
