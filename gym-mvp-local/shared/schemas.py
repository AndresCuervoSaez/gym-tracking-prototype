"""Shared event schemas for the local gym MVP."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    MACHINE_OCCUPIED_START = "MACHINE_OCCUPIED_START"
    MACHINE_OCCUPIED_END = "MACHINE_OCCUPIED_END"
    CLEANING_WINDOW_OPEN = "CLEANING_WINDOW_OPEN"
    CLEANING_ATTEMPT = "CLEANING_ATTEMPT"


class MediaPayload(BaseModel):
    kind: str = "CLIP"
    path: str
    start_ts_utc: float
    end_ts_utc: float


class EventPayload(BaseModel):
    event_id: str
    ts_utc: float
    store_id: str
    camera_id: str
    person_id: str
    track_id: str
    event_type: EventType
    zone_id: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    media: MediaPayload
    needs_mm: bool = False


class EventResponse(EventPayload):
    mm_status: str = "PENDING"
    mm_description: str | None = None
    mm_labels: list[str] = Field(default_factory=list)
    mm_confidence: float | None = None
