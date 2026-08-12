import os
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def _get_test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    parsed = urlparse(url)
    database_name = parsed.path.lstrip("/")
    if database_name != "radar_test":
        raise RuntimeError("Integration tests require TEST_DATABASE_URL to point to database 'radar_test'")
    return url


@pytest.fixture(scope="session")
def integration_engine():
    engine = create_engine(_get_test_database_url(), future=True, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL test database is not available: {exc}")
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(integration_engine):
    factory = sessionmaker(bind=integration_engine, autoflush=False, future=True)
    with factory() as session:
        _truncate_tables(session)
        yield session
        session.rollback()
        _truncate_tables(session)


def _truncate_tables(session: Session) -> None:
    session.execute(
        text(
            """
            TRUNCATE TABLE
                price_history,
                scrape_runs,
                jobs,
                deals,
                company_sources,
                sources
            RESTART IDENTITY CASCADE
            """
        )
    )
    session.commit()

