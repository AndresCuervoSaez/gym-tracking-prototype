"""Backend API for ingesting and querying gym events."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend_api.db import get_session_local, make_engine, make_session_factory
from backend_api.models import Base, Event, Media
from shared.schemas import EventPayload

app = FastAPI(title="gym-mvp-local-backend")
SESSION_FACTORY = None


def event_to_dict(row: Event) -> dict:
    media = row.media
    return {
        "event_id": row.event_id,
        "ts_utc": row.ts_utc,
        "store_id": row.store_id,
        "camera_id": row.camera_id,
        "person_id": row.person_id,
        "track_id": row.track_id,
        "event_type": row.event_type,
        "zone_id": row.zone_id,
        "metrics": row.metrics,
        "needs_mm": row.needs_mm,
        "mm_status": row.mm_status,
        "mm_description": row.mm_description,
        "mm_labels": row.mm_labels or [],
        "mm_confidence": row.mm_confidence,
        "media": {
            "kind": media.kind if media else "CLIP",
            "path": media.path if media else "",
            "start_ts_utc": media.start_ts_utc if media else row.ts_utc,
            "end_ts_utc": media.end_ts_utc if media else row.ts_utc,
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest/event")
def ingest_event(payload: EventPayload) -> dict:
    session = get_session_local(SESSION_FACTORY)
    try:
        existing = session.scalar(select(Event).where(Event.event_id == payload.event_id))
        if existing:
            return {"status": "duplicate", "event_id": payload.event_id}

        event = Event(
            event_id=payload.event_id,
            ts_utc=payload.ts_utc,
            store_id=payload.store_id,
            camera_id=payload.camera_id,
            person_id=payload.person_id,
            track_id=payload.track_id,
            event_type=payload.event_type.value,
            zone_id=payload.zone_id,
            metrics=payload.metrics,
            needs_mm=payload.needs_mm,
            mm_status="PENDING" if payload.needs_mm else "SKIPPED",
        )
        media = Media(
            event_id=payload.event_id,
            kind=payload.media.kind,
            path=payload.media.path,
            start_ts_utc=payload.media.start_ts_utc,
            end_ts_utc=payload.media.end_ts_utc,
        )
        session.add(event)
        session.add(media)
        session.commit()
        return {"status": "created", "event_id": payload.event_id}
    except IntegrityError:
        session.rollback()
        return {"status": "duplicate", "event_id": payload.event_id}
    finally:
        session.close()


@app.get("/events")
def list_events(
    event_type: str | None = None,
    camera_id: str | None = None,
    zone_id: str | None = None,
    start_ts: float | None = Query(default=None),
    end_ts: float | None = Query(default=None),
    limit: int = 200,
):
    session = get_session_local(SESSION_FACTORY)
    try:
        stmt = select(Event).order_by(Event.ts_utc.desc()).limit(limit)
        if event_type:
            stmt = stmt.where(Event.event_type == event_type)
        if camera_id:
            stmt = stmt.where(Event.camera_id == camera_id)
        if zone_id:
            stmt = stmt.where(Event.zone_id == zone_id)
        if start_ts:
            stmt = stmt.where(Event.ts_utc >= start_ts)
        if end_ts:
            stmt = stmt.where(Event.ts_utc <= end_ts)
        rows = session.scalars(stmt).all()
        for row in rows:
            _ = row.media
        return [event_to_dict(r) for r in rows]
    finally:
        session.close()


@app.get("/events/{event_id}")
def get_event(event_id: str):
    session = get_session_local(SESSION_FACTORY)
    try:
        row = session.scalar(select(Event).where(Event.event_id == event_id))
        if not row:
            raise HTTPException(status_code=404, detail="event not found")
        _ = row.media
        return event_to_dict(row)
    finally:
        session.close()


@app.get("/media/{event_id}")
def get_media(event_id: str):
    session = get_session_local(SESSION_FACTORY)
    try:
        media = session.scalar(select(Media).where(Media.event_id == event_id))
        if not media or not Path(media.path).exists():
            raise HTTPException(status_code=404, detail="media not found")
        return FileResponse(media.path, media_type="video/mp4", filename=f"{event_id}.mp4")
    finally:
        session.close()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--media-dir", required=True)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8000)
    return p.parse_args()


def main() -> None:
    global SESSION_FACTORY
    args = parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    Path(args.media_dir).mkdir(parents=True, exist_ok=True)
    engine = make_engine(args.db)
    Base.metadata.create_all(engine)
    SESSION_FACTORY = make_session_factory(engine)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
