"""File-based outbox queue for resilient event delivery."""
from __future__ import annotations

import json
from pathlib import Path


class OutboxQueue:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def enqueue(self, payload: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def read_all(self) -> list[dict]:
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def rewrite(self, payloads: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for payload in payloads:
                f.write(json.dumps(payload) + "\n")
