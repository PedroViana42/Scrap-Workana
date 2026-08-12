import pytest
from sqlalchemy.exc import IntegrityError

from radar.database.models.company_source import CompanySourceDB
from radar.database.repositories.company_sources import CompanySourceRepository
from radar.database.repositories.sources import SourceRepository, sync_source_catalog
from radar.sources.models import CompanySource


pytestmark = pytest.mark.integration


def test_company_source_insert_and_get(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    source = SourceRepository(db_session).get_by_name("greenhouse")
    repository = CompanySourceRepository(db_session)

    company_source = repository.upsert(
        CompanySource(
            company_name="Example",
            source_name="greenhouse",
            external_identifier="example-board",
            country="BR",
            tags=("tech",),
        )
    )
    db_session.commit()

    found = repository.get(source.id, "example-board")

    assert found is not None
    assert found.id == company_source.id
    assert found.company_name == "Example"
    assert found.tags == ["tech"]


def test_company_source_unique_identifier_per_source(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = CompanySourceRepository(db_session)
    source = SourceRepository(db_session).get_by_name("greenhouse")
    repository.upsert(CompanySource("Example", "greenhouse", "same-board"))
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.add(
            CompanySourceDB(
                source_id=source.id,
                company_name="Other",
                external_identifier="same-board",
                tags=[],
                metadata_={},
            )
        )
        db_session.flush()


def test_same_external_identifier_can_exist_in_different_sources(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = CompanySourceRepository(db_session)

    greenhouse = repository.upsert(CompanySource("Example", "greenhouse", "same-board"))
    lever = repository.upsert(CompanySource("Example", "lever", "same-board"))
    db_session.commit()

    assert greenhouse.id != lever.id
    assert greenhouse.source_id != lever.source_id
