from unittest.mock import Mock

import pytest

from radar.config import Settings
from radar.database.repositories.scrape_runs import ScrapeRunRepository, ScrapeRunStatus


def test_database_url_is_required_for_database_operations():
    settings = Settings(database_url=None)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        settings.require_database_url()


def test_scrape_run_finish_updates_status_and_counts():
    session = Mock()
    repository = ScrapeRunRepository(session)
    run = Mock()
    run.started_at = None

    repository.finish(
        run,
        status=ScrapeRunStatus.SUCCESS,
        items_found=10,
        items_new=4,
        items_updated=6,
    )

    assert run.status == "success"
    assert run.items_found == 10
    assert run.items_new == 4
    assert run.items_updated == 6
    assert run.finished_at is not None
    session.flush.assert_called_once()

