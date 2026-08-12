from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from radar.database.models.company_source import CompanySourceDB
from radar.database.repositories.mappers import company_source_to_values
from radar.database.repositories.sources import SourceRepository
from radar.sources.company_catalog import get_company_catalog
from radar.sources.models import CompanySource


class CompanySourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.sources = SourceRepository(session)

    def get(self, source_id: int, external_identifier: str) -> CompanySourceDB | None:
        return self.session.scalar(
            select(CompanySourceDB).where(
                CompanySourceDB.source_id == source_id,
                CompanySourceDB.external_identifier == external_identifier,
            )
        )

    def get_by_id(self, company_source_id: int) -> CompanySourceDB | None:
        return self.session.scalar(
            select(CompanySourceDB)
            .options(joinedload(CompanySourceDB.source))
            .where(CompanySourceDB.id == company_source_id)
        )

    def list_by_source(self, source_id: int) -> list[CompanySourceDB]:
        return list(
            self.session.scalars(
                select(CompanySourceDB).where(CompanySourceDB.source_id == source_id)
            )
        )

    def list_enabled_with_enabled_sources(self) -> list[CompanySourceDB]:
        return list(
            self.session.scalars(
                select(CompanySourceDB)
                .options(joinedload(CompanySourceDB.source))
                .join(CompanySourceDB.source)
                .where(
                    CompanySourceDB.enabled.is_(True),
                    CompanySourceDB.source.has(enabled=True),
                )
                .order_by(CompanySourceDB.id)
            )
        )

    def upsert(self, company_source: CompanySource) -> CompanySourceDB:
        source = self.sources.get_by_name(company_source.source_name)
        if source is None:
            raise ValueError(f"Source not found for company source: {company_source.source_name}")

        values = company_source_to_values(company_source, source.id)
        existing = self.get(source.id, company_source.external_identifier)
        if existing is None:
            existing = CompanySourceDB(**values)
            self.session.add(existing)
            self.session.flush()
            return existing

        for field, value in values.items():
            setattr(existing, field, value)
        self.session.flush()
        return existing


def sync_company_catalog(session: Session) -> list[CompanySourceDB]:
    repository = CompanySourceRepository(session)
    synced: list[CompanySourceDB] = []
    for company_source in get_company_catalog():
        synced.append(repository.upsert(company_source))
    return synced
