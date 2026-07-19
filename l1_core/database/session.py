"""Engine and session factory.

Defaults to a local SQLite file (l1.db) in the current working
directory, which is exactly what the CLI needs: no server, no
config, just a file that lives next to wherever the user runs `l1`
from. Override via the L1_DATABASE_URL environment variable for
tests (in-memory) or a future backend deployment (Postgres, etc).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from l1_core.database.base import Base
from l1_core.database.models import orm_models  # noqa: F401  (registers mappers)

DEFAULT_DATABASE_URL = "sqlite:///l1.db"


def get_engine(database_url: str | None = None):
    url = database_url or os.getenv("L1_DATABASE_URL", DEFAULT_DATABASE_URL)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def init_db(engine) -> None:
    """Creates all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)


def get_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session(database_url: str | None = None) -> Session:
    """Convenience helper for the CLI: one engine + one session per
    invocation. For long-lived processes (e.g. a future API) prefer
    building the engine once and injecting sessions per request."""
    engine = get_engine(database_url)
    init_db(engine)
    factory = get_session_factory(engine)
    return factory()
