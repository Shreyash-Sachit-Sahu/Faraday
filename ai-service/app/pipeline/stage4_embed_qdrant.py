"""Stage 4: embed all chunks with bge-small and upsert them into Qdrant."""

import argparse
from dataclasses import asdict

from tqdm import tqdm

from app import config
from app.pipeline.io_utils import load_all_chunks

EMBED_BATCH = 64
UPSERT_BATCH = 256
VECTOR_SIZE = 384


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed chunk JSONLs and upsert into Qdrant."
    )
    parser.add_argument(
        "--recreate", action="store_true",
        help="drop the collection first if it exists",
    )
    args = parser.parse_args()

    chunks = load_all_chunks(config.DATA_DIR)
    if not chunks:
        raise SystemExit(f"no chunks_*.jsonl content found in {config.DATA_DIR}")
    print(f"chunks loaded: {len(chunks)} from {config.DATA_DIR}")

    import torch  # lazy: heavy dependency
    from sentence_transformers import SentenceTransformer  # lazy: heavy dependency

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"embedding with {config.EMBED_MODEL} on {device}")
    model = SentenceTransformer(config.EMBED_MODEL, device=device)
    vectors = model.encode(
        [chunk.text for chunk in chunks],
        batch_size=EMBED_BATCH,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    from qdrant_client import QdrantClient  # lazy: heavy dependency
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT, timeout=60)
    if args.recreate and client.collection_exists(config.QDRANT_COLLECTION):
        client.delete_collection(config.QDRANT_COLLECTION)
    if not client.collection_exists(config.QDRANT_COLLECTION):
        client.create_collection(
            collection_name=config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    for start in tqdm(
        range(0, len(chunks), UPSERT_BATCH), desc="qdrant upsert", mininterval=5.0
    ):
        batch = chunks[start : start + UPSERT_BATCH]
        points = [
            PointStruct(
                id=chunk.id,
                vector=vectors[start + offset].tolist(),
                payload=asdict(chunk),
            )
            for offset, chunk in enumerate(batch)
        ]
        client.upsert(config.QDRANT_COLLECTION, points=points, wait=True)

    stored = client.count(config.QDRANT_COLLECTION).count
    print(f"chunks read: {len(chunks)} | qdrant count: {stored}")
    if stored != len(chunks):
        raise SystemExit("FAIL: qdrant count does not match chunks read")


if __name__ == "__main__":
    main()
