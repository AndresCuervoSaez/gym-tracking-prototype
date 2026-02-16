"""HTTP sender with retry and outbox flushing."""
from __future__ import annotations

import time

import requests

from edge_service.outbox import OutboxQueue


class EventSender:
    def __init__(self, endpoint: str, outbox: OutboxQueue, timeout_s: float = 2.0):
        self.endpoint = endpoint
        self.outbox = outbox
        self.timeout_s = timeout_s

    def _send_once(self, payload: dict) -> bool:
        try:
            resp = requests.post(self.endpoint, json=payload, timeout=self.timeout_s)
            return resp.status_code in (200, 201)
        except requests.RequestException:
            return False

    def send_with_retry(self, payload: dict, retries: int = 4) -> bool:
        backoff = 0.5
        for _ in range(retries):
            if self._send_once(payload):
                return True
            time.sleep(backoff)
            backoff *= 2
        self.outbox.enqueue(payload)
        return False

    def flush_outbox(self) -> None:
        payloads = self.outbox.read_all()
        remaining = []
        for p in payloads:
            if not self.send_with_retry(p, retries=2):
                remaining.append(p)
        self.outbox.rewrite(remaining)
