"""Video source wrapper with near-real-time pacing."""
from __future__ import annotations

import time
from dataclasses import dataclass

import cv2


@dataclass
class FramePacket:
    frame_idx: int
    frame: any
    ts_utc: float


class VideoSource:
    def __init__(self, path: str, fps_override: float | None = None):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError(f"Unable to open video: {path}")
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 25.0
        self.fps = fps_override or fps
        self._frame_dt = 1.0 / max(self.fps, 1e-6)

    def __iter__(self):
        idx = 0
        while True:
            start = time.time()
            ok, frame = self.cap.read()
            if not ok:
                break
            yield FramePacket(frame_idx=idx, frame=frame, ts_utc=time.time())
            idx += 1
            elapsed = time.time() - start
            if elapsed < self._frame_dt:
                time.sleep(self._frame_dt - elapsed)

    def close(self):
        self.cap.release()
