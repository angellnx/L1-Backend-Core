import pytest

from l1_core.database.session import get_engine, get_session_factory, init_db


@pytest.fixture()
def session():
    """A fresh in-memory SQLite session per test — never touches the
    real l1.db file."""
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    factory = get_session_factory(engine)
    s = factory()
    try:
        yield s
    finally:
        s.close()
