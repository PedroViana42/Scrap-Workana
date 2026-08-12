import pytest

from radar.database.repositories.scrape_runs import ScrapeRunRepository, ScrapeRunStatus
from radar.database.repositories.sources import SourceRepository, sync_source_catalog


pytestmark = pytest.mark.integration


def test_scrape_run_start_and_finish(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    source = SourceRepository(db_session).get_by_name("greenhouse")
    repository = ScrapeRunRepository(db_session)

    run = repository.start(source.id)
    db_session.commit()

    assert run.status == "running"

    finished = repository.finish(
        run,
        status=ScrapeRunStatus.SUCCESS,
        items_found=10,
        items_new=4,
        items_updated=6,
    )
    db_session.commit()

    assert finished.finished_at is not None
    assert finished.status == "success"
    assert finished.items_found == 10
    assert finished.items_new == 4
    assert finished.items_updated == 6
    assert finished.duration_ms is not None

