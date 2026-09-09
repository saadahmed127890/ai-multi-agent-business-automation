import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

TEST_DATABASE_DIR = Path(tempfile.mkdtemp(prefix="ai_multi_agent_tests_"))
TEST_DATABASE_PATH = TEST_DATABASE_DIR / "test_business_automation.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"


from app.database import models  # noqa: E402, F401
from app.database.database import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Generator[None, None, None]:
    """Create an isolated SQLite database for the pytest session."""
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    shutil.rmtree(TEST_DATABASE_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    """Remove all database rows before and after every test."""
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())

    yield

    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session connected to the isolated test database."""
    with SessionLocal() as session:
        yield session
        session.rollback()
