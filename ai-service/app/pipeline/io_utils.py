"""Shared loading helpers for chunk JSONL artifacts."""

from pathlib import Path

from app.pipeline.schema import Chunk


def chunk_files(data_dir: Path) -> list[Path]:
    """All per-source chunk files currently in the data directory."""
    return sorted(data_dir.glob("chunks_*.jsonl"))


def load_all_chunks(data_dir: Path) -> list[Chunk]:
    """Read every chunks_*.jsonl in data_dir into memory, in filename order."""
    chunks: list[Chunk] = []
    for path in chunk_files(data_dir):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    chunks.append(Chunk.from_json(stripped))
    return chunks
