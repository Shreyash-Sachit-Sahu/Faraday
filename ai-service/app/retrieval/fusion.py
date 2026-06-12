"""Reciprocal Rank Fusion of multiple ranked id lists."""


def rrf_fuse(
    rankings: list[list[str]], k: int = 60
) -> list[tuple[str, float]]:
    """Fuse ranked lists (best first) into one ranking.

    score(d) = sum over lists of 1 / (k + rank_in_list(d) + 1), 0-based rank.
    Documents missing from a list simply contribute nothing for that list.
    Returns (doc_id, fused_score) pairs, best first.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


if __name__ == "__main__":
    a = ["d1", "d2", "d3"]
    b = ["d3", "d1", "d4"]
    for doc_id, score in rrf_fuse([a, b]):
        print(f"{doc_id}: {score:.5f}")
