"""Polling worker that applies deterministic VLM mock on pending events."""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend_api.db import get_session_local, make_engine, make_session_factory
from backend_api.models import Event, Media


def vlm_mock(event_id: str, clip_path: str, seed: int) -> tuple[str, list[str], float]:
    rng = random.Random(f"{seed}:{event_id}:{clip_path}")
    labels = ["cleaning", "surface_wipe", "person_present"]
    picked = [labels[i] for i in range(len(labels)) if rng.random() > 0.4]
    picked = picked or ["uncertain"]
    conf = round(0.5 + rng.random() * 0.49, 3)
    desc = f"Mock VLM: detected {', '.join(picked)} with confidence {conf}."
    return desc, picked, conf


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--seed", type=int, default=123)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    engine = make_engine(args.db)
    session_factory = make_session_factory(engine)

    while True:
        session = get_session_local(session_factory)
        try:
            stmt = select(Event).where(Event.needs_mm.is_(True), Event.mm_status == "PENDING").limit(20)
            rows = session.scalars(stmt).all()
            for ev in rows:
                media = session.scalar(select(Media).where(Media.event_id == ev.event_id))
                clip_path = media.path if media else ""
                desc, labels, conf = vlm_mock(ev.event_id, clip_path, args.seed)
                ev.mm_description = desc
                ev.mm_labels = labels
                ev.mm_confidence = conf
                ev.mm_status = "DONE"
            session.commit()
        finally:
            session.close()
        time.sleep(2)


if __name__ == "__main__":
    main()
