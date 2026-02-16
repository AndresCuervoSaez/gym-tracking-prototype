"""Edge service prototype loop for mocked gym behavior events."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from edge_service.clip_buffer import ClipBuffer
from edge_service.event_rules import EventRulesEngine, RuleConfig
from edge_service.mocks import CleaningMotionMock, DetectorMock, TrackerMock
from edge_service.outbox import OutboxQueue
from edge_service.sender import EventSender
from edge_service.video_source import VideoSource
from shared.schemas import EventPayload, MediaPayload
from shared.utils import make_event_id


def point_in_roi(point: tuple[float, float], roi: dict) -> bool:
    x, y = point
    return roi["x1"] <= x <= roi["x2"] and roi["y1"] <= y <= roi["y2"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--camera-id", required=True)
    p.add_argument("--store-id", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--config", default=str(ROOT / "edge_service" / "config.yaml"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    data_dir = ROOT / "data"
    media_dir = data_dir / "media"
    outbox = OutboxQueue(str(data_dir / "outbox.jsonl"))
    sender = EventSender("http://localhost:8000/ingest/event", outbox)

    source = VideoSource(args.video, cfg.get("video_fps_override"))
    clip_buffer = ClipBuffer(source.fps, cfg["clip_pre_s"], cfg["clip_post_s"])
    rules = EventRulesEngine(RuleConfig(cfg["occupy_start_s"], cfg["occupy_end_s"], cfg["cleaning_window_s"]))

    detector = DetectorMock(args.seed)
    tracker = TrackerMock()
    motion = CleaningMotionMock(args.seed)

    for pkt in source:
        frame = pkt.frame
        h, w = frame.shape[:2]
        clip_buffer.push(pkt.ts_utc, frame)
        sender.flush_outbox()

        tracked = tracker.track(detector.detect(pkt.frame_idx, w, h))
        for roi in cfg["rois"]:
            in_zone = [tid for tid, det in tracked if point_in_roi(det.center, roi)]
            evs = rules.process(pkt.ts_utc, roi["zone_id"], in_zone, motion.is_hand_motion(pkt.frame_idx, roi["zone_id"]))
            for ev in evs:
                event_id = make_event_id()
                out_path = media_dir / f"{event_id}.mp4"
                start_ts, end_ts = clip_buffer.export_clip(pkt.ts_utc, str(out_path))
                payload = EventPayload(
                    event_id=event_id,
                    ts_utc=pkt.ts_utc,
                    store_id=args.store_id,
                    camera_id=args.camera_id,
                    person_id="p_0001",
                    track_id=ev.track_id,
                    event_type=ev.event_type,
                    zone_id=ev.zone_id,
                    metrics={"dwell_s": ev.dwell_s},
                    media=MediaPayload(path=str(out_path), start_ts_utc=start_ts, end_ts_utc=end_ts),
                    needs_mm=ev.needs_mm,
                ).model_dump(mode="json")
                print(json.dumps(payload))
                sender.send_with_retry(payload)

    source.close()


if __name__ == "__main__":
    main()
