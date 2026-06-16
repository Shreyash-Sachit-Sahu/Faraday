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

RETRIEVAL_CONCURRENCY: int = int(os.getenv("RETRIEVAL_CONCURRENCY", "8"))
RETRIEVAL_QUEUE_TIMEOUT: float = float(os.getenv("RETRIEVAL_QUEUE_TIMEOUT", "10"))
RETRIEVAL_RERANK_IN: int = int(os.getenv("RETRIEVAL_RERANK_IN", "40"))
RETRIEVAL_CACHE_TTL: int = int(os.getenv("RETRIEVAL_CACHE_TTL", "300"))

GRAPH_NER_MODEL: str = os.getenv("GRAPH_NER_MODEL", "urchade/gliner_small-v2.1")
GRAPH_NER_DEVICE: str = os.getenv("GRAPH_NER_DEVICE", "cpu")
GRAPH_NER_THRESHOLD: float = float(os.getenv("GRAPH_NER_THRESHOLD", "0.5"))
RETRIEVAL_USE_GRAPH: bool = os.getenv("RETRIEVAL_USE_GRAPH", "true").lower() == "true"

BASE_MODEL: str = os.getenv("BASE_MODEL", "google/gemma-2-2b-it")
ADAPTER_DIR: Path = Path(os.getenv("ADAPTER_DIR", str(DATA_DIR / "adapters" / "gemma2-faraday")))
GEN_MAX_NEW_TOKENS: int = int(os.getenv("GEN_MAX_NEW_TOKENS", "1024"))
GEN_TEMPERATURE: float = float(os.getenv("GEN_TEMPERATURE", "0.7"))
GEN_TOP_P: float = float(os.getenv("GEN_TOP_P", "0.9"))
GEN_REPETITION_PENALTY: float = float(os.getenv("GEN_REPETITION_PENALTY", "1.1"))
GEN_LOW_CONF_THRESHOLD: float = float(os.getenv("GEN_LOW_CONF_THRESHOLD", "0.0"))
