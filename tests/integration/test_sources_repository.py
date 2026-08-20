import pytest

from radar.database.repositories.sources import SourceRepository, sync_source_catalog
from radar.sources.types import ContentType


pytestmark = pytest.mark.integration


def test_sync_source_catalog_is_idempotent(db_session):
    first_sync = sync_source_catalog(db_session)
    db_session.commit()
    second_sync = sync_source_catalog(db_session)
    db_session.commit()

    repository = SourceRepository(db_session)
    all_sources = repository.session.query(repository.get_by_name("greenhouse").__class__).all()

    assert len(first_sync) == 14
    assert len(second_sync) == 14
    assert len(all_sources) == 14
    assert repository.get_by_name("workana") is None


def test_source_repository_get_by_name_and_list_enabled(db_session):
    sync_source_catalog(db_session)
    db_session.commit()

    repository = SourceRepository(db_session)
    greenhouse = repository.get_by_name("greenhouse")
    enabled = repository.list_enabled()
    sources = repository.session.query(greenhouse.__class__).all()

    assert greenhouse is not None
    assert greenhouse.content_type == ContentType.JOB.value
    assert greenhouse.enabled is True
    assert {source.name for source in enabled} == {
        "greenhouse",
        "lever",
        "ashby",
        "workable",
        "smartrecruiters",
    }
    assert sum(1 for source in sources if source.content_type == "job") == 10
    assert sum(1 for source in sources if source.content_type == "deal") == 4
