import json
import random
from pathlib import Path

from locust import HttpUser, between, task

from app import config  # run locust from ai-service/ so this imports

QUERIES: list[str] = [
    "Why is quicksort faster than bubble sort in practice?",
    "What happens during the TCP three-way handshake?",
    "Write a Python function to reverse a linked list",
]
evalset = Path(config.DATA_DIR) / "evalset.jsonl"
if evalset.exists():
    with open(evalset, encoding="utf-8") as f:
        QUERIES += [json.loads(line)["query"] for line in f][:200]


class RetrievalUser(HttpUser):
    wait_time = between(0.05, 0.2)

    @task
    def retrieve(self) -> None:
        self.client.post(
            "/retrieve", json={"query": random.choice(QUERIES), "k": 8}
        )
