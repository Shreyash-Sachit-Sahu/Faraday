import json
import uuid
from dataclasses import asdict, dataclass

NAMESPACE = uuid.UUID("d9b2d63d-a233-4123-847a-717d672f3f1e")


@dataclass
class Chunk:
    id: str
    text: str
    source: str  # "wikipedia" | "mmlu" | "codealpaca" | (later: "upload")
    title: str
    doc_id: str
    chunk_index: int
    url: str = ""
    owner_id: str = "global"  # "global" = shared corpus; later: uploader's user id
    doc_kind: str = "corpus"  # "corpus" | "upload"

    @staticmethod
    def make_id(source: str, doc_id: str, chunk_index: int) -> str:
        return str(uuid.uuid5(NAMESPACE, f"{source}:{doc_id}:{chunk_index}"))

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def from_json(line: str) -> "Chunk":
        return Chunk(**json.loads(line))
