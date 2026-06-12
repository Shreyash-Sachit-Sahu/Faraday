"""Paragraph chunking rules for corpus documents (PHASE1.md section 5)."""

MIN_PARAGRAPH_CHARS = 40
MAX_PARAGRAPH_CHARS = 2500
MAX_CHUNK_CHARS = 1100
MIN_FINAL_CHUNK_CHARS = 200


def chunk_text(title: str, text: str) -> list[str]:
    """Split text into title-prefixed chunks of at most ~MAX_CHUNK_CHARS bodies."""
    paragraphs: list[str] = []
    for raw in text.split("\n\n"):
        para = raw.strip()
        if len(para) < MIN_PARAGRAPH_CHARS:
            continue
        paragraphs.append(para[:MAX_PARAGRAPH_CHARS])

    bodies: list[str] = []
    buffer: list[str] = []
    buffer_len = 0
    for para in paragraphs:
        candidate_len = len(para) if not buffer else buffer_len + 2 + len(para)
        if buffer and candidate_len > MAX_CHUNK_CHARS:
            bodies.append("\n\n".join(buffer))
            buffer = [para]
            buffer_len = len(para)
        else:
            buffer.append(para)
            buffer_len = candidate_len
    if buffer:
        tail = "\n\n".join(buffer)
        if len(tail) < MIN_FINAL_CHUNK_CHARS and bodies:
            bodies[-1] = f"{bodies[-1]}\n\n{tail}"
        else:
            bodies.append(tail)

    return [f"{title}\n\n{body}" for body in bodies]


if __name__ == "__main__":
    demo = "\n\n".join(
        [
            "Quicksort is a divide-and-conquer sorting algorithm that picks a pivot "
            "element and partitions the array around it, recursing on both sides. "
            "Its average-case running time is O(n log n) with small constants.",
            "Merge sort also divides the input, but instead of partitioning it merges "
            "two sorted halves; it guarantees O(n log n) in the worst case at the "
            "cost of extra memory for the merge step.",
            "Heapsort builds a binary heap and repeatedly extracts the maximum, "
            "giving an in-place O(n log n) sort that is not stable.",
        ]
    )
    for i, chunk in enumerate(chunk_text("Sorting algorithms", demo)):
        print(f"--- chunk {i} ({len(chunk)} chars) ---")
        print(chunk)
