"""Deterministic mock detector/tracker and cleaning classifier."""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


class DetectorMock:
    """Creates deterministic pseudo-person detections with persistent trajectories."""

    def __init__(self, seed: int):
        self.rand = random.Random(seed)

    def detect(self, frame_idx: int, width: int, height: int) -> list[Detection]:
        count = (frame_idx // 40) % 3  # cycles 0-2 persons
        dets: list[Detection] = []
        for i in range(count + 1):
            x = 80 + i * 90 + int(20 * self.rand.uniform(-1, 1)) + (frame_idx % 30)
            y = 130 + i * 30
            w, h = 60, 180
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(width - 1, x + w), min(height - 1, y + h)
            dets.append(Detection(x1, y1, x2, y2))
        return dets


class TrackerMock:
    def __init__(self):
        self._active: dict[int, str] = {}

    def track(self, detections: list[Detection]) -> list[tuple[str, Detection]]:
        tracked: list[tuple[str, Detection]] = []
        for idx, det in enumerate(detections):
            if idx not in self._active:
                self._active[idx] = f"t_{idx+1:04d}"
            tracked.append((self._active[idx], det))
        return tracked


class CleaningMotionMock:
    def __init__(self, seed: int):
        self.rand = random.Random(seed + 999)

    def is_hand_motion(self, frame_idx: int, zone_id: str) -> bool:
        threshold = 0.85 if zone_id else 0.95
        return ((frame_idx % 10) == 0) or self.rand.random() > threshold
