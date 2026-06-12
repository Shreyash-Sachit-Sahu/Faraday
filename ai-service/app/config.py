import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

QDRANT_HOST: str = os.getenv("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(ROOT / "ai-service" / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
QDRANT_COLLECTION: str = "faraday_chunks"
