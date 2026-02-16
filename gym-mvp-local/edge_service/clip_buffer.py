"""In-memory ring buffer for exporting event clips."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2


@dataclass
class BufferedFrame:
    ts_utc: float
    frame: any


class ClipBuffer:
    def __init__(self, fps: float, pre_s: float, post_s: float):
        self.fps = fps
        self.pre_s = pre_s
        self.post_s = post_s
        self.buffer = deque(maxlen=int(fps * (pre_s + post_s + 2)))

    def push(self, ts_utc: float, frame: any) -> None:
        self.buffer.append(BufferedFrame(ts_utc=ts_utc, frame=frame.copy()))

    def export_clip(self, event_ts: float, out_path: str) -> tuple[float, float]:
        start = event_ts - self.pre_s
        end = event_ts + self.post_s
        frames = [bf for bf in self.buffer if start <= bf.ts_utc <= end]
        if not frames:
            return start, end

        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        h, w = frames[0].frame.shape[:2]
        writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (w, h))
        for bf in frames:
            writer.write(bf.frame)
        writer.release()
        return frames[0].ts_utc, frames[-1].ts_utc
