from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from radar.database.repositories.scrape_runs import ScrapeRunStatus
from radar.scheduler.cycle import company_interval_minutes, list_due_company_sources, run_scheduler_cycle
from radar.services.job_collection import JobCollectionService


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


def _company_source(id_, source_name="greenhouse", enabled=True, source_enabled=True, interval=60, metadata=None):
    return SimpleNamespace(
        id=id_,
        company_name=f"Company {id_}",
        external_identifier=f"company-{id_}",
        enabled=enabled,
        metadata_=metadata or {},
        source=SimpleNamespace(id=10 + id_, name=source_name, enabled=source_enabled, interval_minutes=interval),
    )


def _run(finished_at, status=ScrapeRunStatus.SUCCESS):
    return SimpleNamespace(finished_at=finished_at, status=status.value)


def test_company_interval_uses_metadata_override():
    company_source = _company_source(1, interval=60, metadata={"interval_minutes": 15})

    assert company_interval_minutes(company_source) == 15


def test_never_run_is_due(monkeypatch):
    company_source = _company_source(1)
    monkeypatch.setattr(
        "radar.scheduler.cycle.CompanySourceRepository.list_enabled_with_enabled_sources",
        lambda self: [company_source],
    )
    monkeypatch.setattr("radar.scheduler.cycle.ScrapeRunRepository.get_last_run", lambda self, company_source_id: None)

    due = list_due_company_sources(SimpleNamespace(), now=NOW)

    assert [item.company_source.id for item in due] == [1]


def test_interval_not_elapsed_is_not_due(monkeypatch):
    company_source = _company_source(1)
    monkeypatch.setattr(
        "radar.scheduler.cycle.CompanySourceRepository.list_enabled_with_enabled_sources",
        lambda self: [company_source],
    )
    monkeypatch.setattr(
        "radar.scheduler.cycle.ScrapeRunRepository.get_last_run",
        lambda self, company_source_id: _run(NOW - timedelta(minutes=30)),
    )

    assert list_due_company_sources(SimpleNamespace(), now=NOW) == []


def test_failed_run_still_applies_cooldown(monkeypatch):
    company_source = _company_source(1)
    monkeypatch.setattr(
        "radar.scheduler.cycle.CompanySourceRepository.list_enabled_with_enabled_sources",
        lambda self: [company_source],
    )
    monkeypatch.setattr(
        "radar.scheduler.cycle.ScrapeRunRepository.get_last_run",
        lambda self, company_source_id: _run(NOW - timedelta(minutes=30), ScrapeRunStatus.FAILED),
    )

    assert list_due_company_sources(SimpleNamespace(), now=NOW) == []


def test_due_order_and_batch_limit(monkeypatch):
    companies = [_company_source(1), _company_source(2), _company_source(3)]
    last_runs = {
        1: _run(NOW - timedelta(hours=4)),
        2: _run(NOW - timedelta(hours=2)),
        3: _run(NOW - timedelta(hours=3)),
    }
    monkeypatch.setattr(
        "radar.scheduler.cycle.CompanySourceRepository.list_enabled_with_enabled_sources",
        lambda self: companies,
    )
    monkeypatch.setattr(
        "radar.scheduler.cycle.ScrapeRunRepository.get_last_run",
        lambda self, company_source_id: last_runs[company_source_id],
    )

    result = run_scheduler_cycle(SimpleNamespace(), dry_run=True, max_companies=2)

    assert result.due_count == 3
    assert result.would_process == 2
    assert [item.company_source.id for item in result.due or []] == [1, 3]


def test_lifecycle_guards_classify_partial_results(monkeypatch):
    service = JobCollectionService.__new__(JobCollectionService)
    monkeypatch.setenv("RADAR_LIFECYCLE_MIN_RESULT_RATIO", "0.20")

    assert service._classify_result(items_found=0, active_before=3) == (
        ScrapeRunStatus.PARTIAL,
        "SuspiciousEmptyResult",
    )
    assert service._classify_result(items_found=1, active_before=10) == (
        ScrapeRunStatus.PARTIAL,
        "SuspiciousResultDrop",
    )
    assert service._classify_result(items_found=8, active_before=10) == (ScrapeRunStatus.SUCCESS, None)
