from sqlalchemy import select
from sqlalchemy.orm import Session

from radar.database.models.source import SourceDB
from radar.database.repositories.mappers import source_config_to_values
from radar.sources.catalog import list_sources
from radar.sources.models import SourceConfig


class SourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(self, name: str) -> SourceDB | None:
        return self.session.scalar(select(SourceDB).where(SourceDB.name == name.lower().strip()))

    def list_enabled(self) -> list[SourceDB]:
        return list(self.session.scalars(select(SourceDB).where(SourceDB.enabled.is_(True))))

    def list_all(self) -> list[SourceDB]:
        return list(self.session.scalars(select(SourceDB).order_by(SourceDB.priority, SourceDB.name)))

    def upsert(self, source: SourceConfig) -> SourceDB:
        values = source_config_to_values(source)
        existing = self.get_by_name(source.name)
        if existing is None:
            existing = SourceDB(**values)
            self.session.add(existing)
            self.session.flush()
            return existing

        for field, value in values.items():
            setattr(existing, field, value)
        self.session.flush()
        return existing


def sync_source_catalog(session: Session) -> list[SourceDB]:
    repository = SourceRepository(session)
    synced: list[SourceDB] = []
    for source in list_sources():
        synced.append(repository.upsert(source))
    return synced

