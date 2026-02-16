"""Shared helper utilities."""
from __future__ import annotations

import time
import uuid


def utc_ts() -> float:
    return time.time()


def make_event_id() -> str:
    return str(uuid.uuid4())
