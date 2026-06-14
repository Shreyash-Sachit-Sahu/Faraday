"""Step C: extract CS entities from every chunk with GLiNER (resumable GPU job)."""

import argparse
import json
from collections import Counter

from tqdm import tqdm

from app import config
from app.graph.entities import (
    ENTITY_LABELS,
    get_ner_model,
    keep_entity,
    normalize_entity,
)
from app.pipeline.io_utils import load_all_chunks

OUT_NAME = "chunk_entities.jsonl"

batch_chunks: list[dict] = []  # each: {"id","source","owner_id","text"}


def flush(batch, model, out_f):
    if not batch:
        return 0
    texts = [c["text"][:1500] for c in batch]
    preds = model.batch_predict_entities(
        texts, ENTITY_LABELS, threshold=config.GRAPH_NER_THRESHOLD
    )
    for chunk, ents in zip(batch, preds):
        best: dict[str, dict] = {}
        for e in ents:
            name = normalize_entity(e["text"])
            if not keep_entity(name):
                continue
            if name not in best or e["score"] > best[name]["score"]:
                best[name] = {
                    "name": name,
                    "display": e["text"].strip(),
                    "label": e["label"],
                    "score": round(float(e["score"]), 3),
                }
        out_f.write(
            json.dumps(
                {
                    "chunk_id": chunk["id"],
                    "source": chunk["source"],
                    "owner_id": chunk.get("owner_id", "global"),
                    "entities": list(best.values()),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    out_f.flush()
    return len(batch)


def _load_done_ids(out_path) -> set[str]:
    """Collect chunk_ids already written so a re-run resumes instead of redoing."""
    done: set[str] = set()
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    done.add(json.loads(line)["chunk_id"])
    return done


def _corpus_stats(out_path) -> tuple[int, float, list[tuple[str, int]]]:
    """Total lines, mean entities/chunk, and the 15 most frequent entity displays."""
    total = 0
    entity_total = 0
    freq: Counter = Counter()
    with open(out_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            total += 1
            ents = row["entities"]
            entity_total += len(ents)
            for ent in ents:
                freq[ent["display"]] += 1
    mean = entity_total / total if total else 0.0
    return total, mean, freq.most_common(15)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CS entities with GLiNER.")
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--limit", type=int, default=0, help="0 = all chunks")
    parser.add_argument(
        "--threshold", type=float, default=config.GRAPH_NER_THRESHOLD
    )
    args = parser.parse_args()
    config.GRAPH_NER_THRESHOLD = args.threshold

    out_path = config.DATA_DIR / OUT_NAME
    done = _load_done_ids(out_path)

    chunks = load_all_chunks(config.DATA_DIR)
    todo = [c for c in chunks if c.id not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(
        f"chunks total: {len(chunks)} | already done: {len(done)} | "
        f"to process this run: {len(todo)} (device={args.device})"
    )

    model = get_ner_model(device=args.device)

    processed = 0
    with open(out_path, "a", encoding="utf-8") as out_f:
        batch: list[dict] = []
        for chunk in tqdm(todo, desc="extract", mininterval=5.0):
            batch.append(
                {
                    "id": chunk.id,
                    "source": chunk.source,
                    "owner_id": chunk.owner_id,
                    "text": chunk.text,
                }
            )
            if len(batch) >= args.batch_size:
                processed += flush(batch, model, out_f)
                batch = []
        processed += flush(batch, model, out_f)

    total, mean, top15 = _corpus_stats(out_path)
    print(
        f"processed this run: {processed} | skipped (already done): {len(done)} | "
        f"total lines: {total} | mean entities/chunk: {mean:.2f}"
    )
    print("15 most frequent entities:")
    for display, count in top15:
        print(f"  {count:6d}  {display}")


if __name__ == "__main__":
    main()
