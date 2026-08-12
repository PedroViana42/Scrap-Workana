from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorHTTPError
from radar.collectors.registry import CollectorRegistry
from radar.database.models.job import JobDB
from radar.database.models.scrape_run import ScrapeRunDB
from radar.database.repositories.company_sources import CompanySourceRepository
from radar.database.repositories.sources import sync_source_catalog
from radar.models import EmploymentType, Job, RemoteType, Seniority
from radar.scheduler.cycle import list_due_company_sources, run_scheduler_cycle
from radar.scheduler.locking import RadarSchedulerLock
from radar.services.job_collection import JobCollectionService
from radar.sources.models import CompanySource


pytestmark = pytest.mark.integration


class SequenceCollector(BaseCollector[CollectorResult]):
    source_name = "greenhouse"
    batches: list[list[str]] = []

    def __init__(self, company_source):
        self.company_source = company_source

    def collect(self) -> CollectorResult:
        batch = self.batches.pop(0)
        jobs = [
            CollectedJob(
                job=Job(
                    source="greenhouse",
                    external_id=external_id,
                    title=f"Backend Engineer {external_id}",
                    company=self.company_source.company_name,
                    description="Python PostgreSQL",
                    url=f"https://example.com/{external_id}",
                    remote_type=RemoteType.REMOTE,
                    employment_type=EmploymentType.FULL_TIME,
                    seniority=Seniority.UNKNOWN,
                    collected_at=datetime.now(timezone.utc),
                ),
                raw_data={"id": external_id},
            )
            for external_id in batch
        ]
        return CollectorResult(source_name="greenhouse", company_source=self.company_source, jobs=jobs)


class EmptyCollector(SequenceCollector):
    batches = [[]]


class FailingCollector(BaseCollector[CollectorResult]):
    source_name = "greenhouse"

    def __init__(self, company_source):
        self.company_source = company_source

    def collect(self) -> CollectorResult:
        raise CollectorHTTPError("temporary failure")


def _registry(collector_cls):
    registry = CollectorRegistry()
    registry.register("greenhouse", collector_cls)
    return registry


def _sync_company(db_session) -> CompanySource:
    sync_source_catalog(db_session)
    company_source = CompanySource("Example", "greenhouse", "example-board")
    CompanySourceRepository(db_session).upsert(company_source)
    db_session.commit()
    return company_source


def test_migration_0003_columns_exist(db_session):
    rows = db_session.execute(
        text(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE (table_name = 'jobs' AND column_name = 'deactivated_at')
               OR (table_name = 'scrape_runs' AND column_name IN ('company_source_id', 'items_deactivated'))
            """
        )
    ).all()

    assert {tuple(row) for row in rows} == {
        ("jobs", "deactivated_at"),
        ("scrape_runs", "company_source_id"),
        ("scrape_runs", "items_deactivated"),
    }


def test_advisory_lock_is_singleton(integration_engine):
    first = RadarSchedulerLock(integration_engine, lock_key=987654)
    second = RadarSchedulerLock(integration_engine, lock_key=987654)

    assert first.acquire() is True
    assert second.acquire() is False
    first.release()
    assert second.acquire() is True
    second.release()


def test_lifecycle_two_successful_misses_deactivate_and_reappearance_reactivates(db_session):
    company_source = _sync_company(db_session)
    SequenceCollector.batches = [["a", "b"], ["b"], ["b"], ["a", "b"]]
    service = JobCollectionService(db_session, registry=_registry(SequenceCollector))

    first = service.collect_and_persist(company_source)
    second = service.collect_and_persist(company_source)
    third = service.collect_and_persist(company_source)
    inactive_job = db_session.query(JobDB).filter(JobDB.external_id == "a").one()

    assert first.items_deactivated == 0
    assert second.items_deactivated == 0
    assert third.items_deactivated == 1
    assert inactive_job.active is False
    assert inactive_job.deactivated_at is not None

    original_first_seen_at = inactive_job.first_seen_at
    fourth = service.collect_and_persist(company_source)
    reactivated_job = db_session.query(JobDB).filter(JobDB.external_id == "a").one()

    assert fourth.items_deactivated == 0
    assert reactivated_job.active is True
    assert reactivated_job.deactivated_at is None
    assert reactivated_job.first_seen_at == original_first_seen_at
    assert reactivated_job.last_seen_at > inactive_job.first_seen_at


def test_partial_empty_result_does_not_advance_lifecycle(db_session):
    company_source = _sync_company(db_session)
    SequenceCollector.batches = [["a", "b"], [], ["b"]]
    service = JobCollectionService(db_session, registry=_registry(SequenceCollector))

    service.collect_and_persist(company_source)
    partial = service.collect_and_persist(company_source)
    success_after_partial = service.collect_and_persist(company_source)
    job = db_session.query(JobDB).filter(JobDB.external_id == "a").one()

    assert partial.status.value == "partial"
    assert partial.lifecycle_guard == "SuspiciousEmptyResult"
    assert success_after_partial.items_deactivated == 0
    assert job.active is True


def test_failed_run_does_not_advance_lifecycle(db_session):
    company_source = _sync_company(db_session)
    SequenceCollector.batches = [["a", "b"], ["b"]]
    service = JobCollectionService(db_session, registry=_registry(SequenceCollector))

    service.collect_and_persist(company_source)
    with pytest.raises(CollectorHTTPError):
        JobCollectionService(db_session, registry=_registry(FailingCollector)).collect_and_persist(company_source)
    second_success = service.collect_and_persist(company_source)
    job = db_session.query(JobDB).filter(JobDB.external_id == "a").one()

    assert second_success.items_deactivated == 0
    assert job.active is True


def test_due_queries_and_scheduler_once_with_fake_collector(db_session):
    company_source = _sync_company(db_session)
    due = list_due_company_sources(db_session)

    assert len(due) == 1
    assert due[0].company_source.company_name == "Example"

    SequenceCollector.batches = [["a"]]
    result = run_scheduler_cycle(db_session, max_companies=1, registry=_registry(SequenceCollector))

    run = db_session.query(ScrapeRunDB).one()
    job = db_session.query(JobDB).one()

    assert len(result.processed) == 1
    assert run.company_source_id is not None
    assert run.items_found == 1
    assert run.items_deactivated == 0
    assert job.relevance_score is not None
    assert job.relevance_version == "tech_early_career_br:v1.1"


def test_due_respects_finished_at_cooldown_for_success_and_failed(db_session):
    company_source = _sync_company(db_session)
    SequenceCollector.batches = [["a"]]
    service = JobCollectionService(db_session, registry=_registry(SequenceCollector))
    service.collect_and_persist(company_source)

    assert list_due_company_sources(db_session) == []

    run = db_session.query(ScrapeRunDB).one()
    run.status = "failed"
    run.finished_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    db_session.commit()

    assert list_due_company_sources(db_session) == []
