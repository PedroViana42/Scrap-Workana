from collections.abc import Iterator

from sqlalchemy.orm import Session

from radar.database.session import create_session_factory


SessionFactory = create_session_factory


def get_session() -> Iterator[Session]:
    factory = SessionFactory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
