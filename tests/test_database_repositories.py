from unittest.mock import Mock

import pytest

from radar.config import Settings
from radar.database.models.job import JobDB
from radar.database.repositories.jobs import JobRepository, JobSearchFilters
from radar.database.repositories.scrape_runs import ScrapeRunRepository, ScrapeRunStatus
from radar.database.repositories.stats import StatsRepository
from sqlalchemy import select


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


def test_stats_relevance_bands_are_normalized_to_lowercase():
    session = Mock()
    session.execute.return_value = [("STRONG", 2), ("VERY_LOW", 3)]

    result = StatsRepository(session).jobs_by_relevance_band()

    assert result["strong"] == 2
    assert result["very_low"] == 3
    assert "STRONG" not in result


def test_relevance_band_filter_is_case_insensitive():
    repository = JobRepository(Mock())

    statement = repository._apply_search_filters(
        select(JobDB),
        JobSearchFilters(relevance_band="strong", active=None),
    )

    assert "lower(jobs.relevance_band)" in str(statement)


def test_attainability_filter_uses_persisted_typed_signal():
    repository = JobRepository(Mock())

    statement = repository._apply_search_filters(
        select(JobDB),
        JobSearchFilters(attainability="HIGH", active=None),
    )

    compiled = str(statement)
    assert "relevance_reasons" in compiled
    assert "upper" in compiled.lower()
