import pytest

from radar.database.models.company_source import CompanySourceDB
from radar.database.repositories.company_sources import sync_company_catalog
from radar.database.repositories.sources import sync_source_catalog
from radar.sources.company_catalog import get_company_catalog


pytestmark = pytest.mark.integration


def test_sync_company_catalog_is_idempotent(db_session):
    sync_source_catalog(db_session)
    first = sync_company_catalog(db_session)
    db_session.commit()
    second = sync_company_catalog(db_session)
    db_session.commit()

    expected = len(get_company_catalog())

    assert len(first) == expected
    assert len(second) == expected
    assert db_session.query(CompanySourceDB).count() == expected
    assert db_session.query(CompanySourceDB).filter(CompanySourceDB.enabled.is_(True)).count() == expected

