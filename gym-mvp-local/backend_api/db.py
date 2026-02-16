"""Database setup helpers for backend and worker."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def make_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}", future=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session_local(session_factory) -> Session:
    return session_factory()
