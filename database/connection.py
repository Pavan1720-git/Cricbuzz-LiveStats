"""
database/connection.py — SQLAlchemy engine factory.

Supports both MySQL (production) and SQLite (development / fallback).
All other modules import `get_engine()` and `get_session()` from here.
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATABASE_URL

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def _configure_sqlite(engine):
    """Enable WAL mode and foreign-key enforcement for SQLite connections."""
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine(database_url: str = DATABASE_URL):
    """Return a cached SQLAlchemy engine.  Tries MySQL; falls back to SQLite."""
    global _engine
    if _engine is not None:
        return _engine

    url = database_url or DATABASE_URL

    try:
        kwargs = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["pool_pre_ping"] = True
            kwargs["pool_size"] = 5
            kwargs["max_overflow"] = 10

        eng = create_engine(url, **kwargs)
        # Test connectivity
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))

        if url.startswith("sqlite"):
            _configure_sqlite(eng)

        logger.info("Database connected: %s", url.split("@")[-1])
        _engine = eng
        return _engine

    except OperationalError as exc:
        logger.warning("Primary DB failed (%s). Falling back to SQLite.", exc)
        fallback = "sqlite:///cricbuzz.db"
        eng = create_engine(fallback, connect_args={"check_same_thread": False})
        _configure_sqlite(eng)
        _engine = eng
        return _engine


def get_session() -> Session:
    """Return a new database session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal()


def reset_engine():
    """Force a new engine on next call (used in tests)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
