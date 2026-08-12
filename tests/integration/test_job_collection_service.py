from datetime import datetime, timezone

import pytest

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorHTTPError
from radar.collectors.registry import CollectorRegistry
from radar.database.models.job import JobDB
from radar.database.models.scrape_run import ScrapeRunDB
from radar.database.repositories.sources import sync_source_catalog
from radar.models import EmploymentType, Job, RemoteType, Seniority
from radar.services.job_collection import JobCollectionService
from radar.sources.models import CompanySource


pytestmark = pytest.mark.integration


class FakeSuccessCollector(BaseCollector[CollectorResult]):
    source_name = "greenhouse"

    def __init__(self, company_source):
        self.company_source = company_source

    def collect(self) -> CollectorResult:
        job = Job(
            source="greenhouse",
            external_id="fake-1",
            title="Backend Engineer",
            company=self.company_source.company_name,
            description="Python",
            url="https://example.com/fake-1",
            remote_type=RemoteType.REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            seniority=Seniority.UNKNOWN,
            collected_at=datetime.now(timezone.utc),
        )
        return CollectorResult(
            source_name="greenhouse",
            company_source=self.company_source,
            jobs=[CollectedJob(job=job, raw_data={"id": "fake-1"})],
        )


class FakeFailingCollector(BaseCollector[CollectorResult]):
    source_name = "greenhouse"

    def __init__(self, company_source):
        self.company_source = company_source

    def collect(self) -> CollectorResult:
        raise CollectorHTTPError("source unavailable")


def _registry(collector_cls):
    registry = CollectorRegistry()
    registry.register("greenhouse", collector_cls)
    return registry


def test_job_collection_success_records_run_and_upserts_jobs(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    service = JobCollectionService(db_session, registry=_registry(FakeSuccessCollector))

    summary = service.collect_and_persist(
        CompanySource("Example", "greenhouse", "example-board"),
        persist_company_source=True,
    )

    run = db_session.query(ScrapeRunDB).one()
    job = db_session.query(JobDB).one()

    assert summary.status.value == "success"
    assert summary.items_found == 1
    assert summary.items_new == 1
    assert summary.items_updated == 0
    assert run.status == "success"
    assert run.items_found == 1
    assert job.title == "Backend Engineer"
    assert job.raw_data == {"id": "fake-1"}


def test_job_collection_second_run_counts_updated(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    service = JobCollectionService(db_session, registry=_registry(FakeSuccessCollector))
    company_source = CompanySource("Example", "greenhouse", "example-board")

    service.collect_and_persist(company_source)
    summary = service.collect_and_persist(company_source)

    assert summary.items_new == 0
    assert summary.items_updated == 1
    assert db_session.query(JobDB).count() == 1
    assert db_session.query(ScrapeRunDB).count() == 2


def test_job_collection_failure_records_failed_run(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    service = JobCollectionService(db_session, registry=_registry(FakeFailingCollector))

    with pytest.raises(CollectorHTTPError):
        service.collect_and_persist(CompanySource("Example", "greenhouse", "example-board"))

    run = db_session.query(ScrapeRunDB).one()
    assert run.status == "failed"
    assert run.error_type == "CollectorHTTPError"
    assert "source unavailable" in run.error_message

