"""SQLAlchemy ORM models."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend_api.db import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    ts_utc: Mapped[float] = mapped_column(Float, index=True)
    store_id: Mapped[str] = mapped_column(String)
    camera_id: Mapped[str] = mapped_column(String, index=True)
    person_id: Mapped[str] = mapped_column(String)
    track_id: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String, index=True)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    needs_mm: Mapped[bool] = mapped_column(Boolean, default=False)
    mm_status: Mapped[str] = mapped_column(String, default="PENDING")
    mm_description: Mapped[str | None] = mapped_column(String, nullable=True)
    mm_labels: Mapped[list] = mapped_column(JSON, default=list)
    mm_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    media: Mapped["Media | None"] = relationship("Media", back_populates="event", uselist=False)


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.event_id"), unique=True)
    kind: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    start_ts_utc: Mapped[float] = mapped_column(Float)
    end_ts_utc: Mapped[float] = mapped_column(Float)

    event: Mapped[Event] = relationship("Event", back_populates="media")
