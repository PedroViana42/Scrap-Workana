from dataclasses import dataclass
import os

from sqlalchemy.orm import Session

from radar.collectors.base import CollectorResult
from radar.collectors.errors import CollectorError
from radar.collectors.registry import CollectorRegistry, default_registry
from radar.database.models.company_source import CompanySourceDB
from radar.database.repositories.company_sources import CompanySourceRepository
from radar.database.repositories.jobs import JobRepository
from radar.database.repositories.scrape_runs import ScrapeRunRepository, ScrapeRunStatus
from radar.database.repositories.sources import SourceRepository
from radar.relevance.scoring import score_job
from radar.sources.models import CompanySource


@dataclass
class JobCollectionSummary:
    source_name: str
    company_name: str
    items_found: int
    items_new: int
    items_updated: int
    items_deactivated: int
    status: ScrapeRunStatus
    scrape_run_id: int | None = None
    lifecycle_guard: str | None = None


class JobCollectionService:
    def __init__(self, session: Session, registry: CollectorRegistry | None = None) -> None:
        self.session = session
        self.registry = registry or default_registry
        self.sources = SourceRepository(session)
        self.company_sources = CompanySourceRepository(session)
        self.jobs = JobRepository(session)
        self.scrape_runs = ScrapeRunRepository(session)

    def collect_and_persist(
        self,
        company_source: CompanySource,
        persist_company_source: bool = False,
    ) -> JobCollectionSummary:
        source = self.sources.get_by_name(company_source.source_name)
        if source is None:
            raise ValueError(f"Source not found: {company_source.source_name}. Run sync-sources first.")

        company_source_id: int | None = None
        if persist_company_source:
            company_source_db = self.company_sources.upsert(company_source)
            company_source_id = company_source_db.id
        else:
            company_source_db = self.company_sources.get(source.id, company_source.external_identifier)
            if company_source_db is not None:
                company_source_id = company_source_db.id

        run = self.scrape_runs.start(
            source.id,
            company_source_id=company_source_id,
            metadata={
                "company_name": company_source.company_name,
                "external_identifier": company_source.external_identifier,
            },
        )
        self.session.flush()

        try:
            result = self._collect(company_source)
            items_new = 0
            items_updated = 0
            items_deactivated = 0
            active_before = self.jobs.count_active_by_company_source(company_source_id) if company_source_id else 0
            for collected_job in result.jobs:
                if run.started_at and collected_job.job.collected_at < run.started_at:
                    collected_job.job.collected_at = run.started_at
                job_db, created = self.jobs.upsert(
                    collected_job.job,
                    company_source_id=company_source_id,
                    raw_data=collected_job.raw_data,
                )
                relevance = score_job(collected_job.job)
                self.jobs.update_relevance(job_db.id, relevance, technologies=collected_job.job.technologies)
                if created:
                    items_new += 1
                else:
                    items_updated += 1

            status, lifecycle_guard = self._classify_result(result.items_found, active_before)
            metadata = {
                "company_name": company_source.company_name,
                "external_identifier": company_source.external_identifier,
            }
            if lifecycle_guard:
                metadata["lifecycle_guard"] = lifecycle_guard

            if status is ScrapeRunStatus.SUCCESS and company_source_id is not None:
                items_deactivated = self._apply_lifecycle(company_source_id)

            self.scrape_runs.finish(
                run,
                status=status,
                items_found=result.items_found,
                items_new=items_new,
                items_updated=items_updated,
                items_deactivated=items_deactivated,
                metadata=metadata,
            )
            self.session.commit()
            return JobCollectionSummary(
                source_name=company_source.source_name,
                company_name=company_source.company_name,
                items_found=result.items_found,
                items_new=items_new,
                items_updated=items_updated,
                items_deactivated=items_deactivated,
                status=status,
                scrape_run_id=run.id,
                lifecycle_guard=lifecycle_guard,
            )
        except Exception as exc:
            self.session.rollback()
            run = self.scrape_runs.start(
                source.id,
                company_source_id=company_source_id,
                metadata={
                    "company_name": company_source.company_name,
                    "external_identifier": company_source.external_identifier,
                },
            )
            self.scrape_runs.finish(
                run,
                status=ScrapeRunStatus.FAILED,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            self.session.commit()
            raise

    def dry_run(self, company_source: CompanySource) -> CollectorResult:
        return self._collect(company_source)

    def _collect(self, company_source: CompanySource) -> CollectorResult:
        collector_cls = self.registry.get(company_source.source_name)
        collector = collector_cls(company_source=company_source)
        result = collector.collect()
        if not isinstance(result, CollectorResult):
            raise CollectorError("Collector returned an invalid result")
        return result

    def _classify_result(self, items_found: int, active_before: int) -> tuple[ScrapeRunStatus, str | None]:
        if active_before > 0 and items_found == 0:
            return ScrapeRunStatus.PARTIAL, "SuspiciousEmptyResult"
        min_ratio = float(os.getenv("RADAR_LIFECYCLE_MIN_RESULT_RATIO", "0.20"))
        if active_before >= 10 and items_found < active_before * min_ratio:
            return ScrapeRunStatus.PARTIAL, "SuspiciousResultDrop"
        return ScrapeRunStatus.SUCCESS, None

    def _apply_lifecycle(self, company_source_id: int) -> int:
        previous_success = self.scrape_runs.get_last_successful_run(company_source_id)
        if previous_success is None:
            return 0
        missing_jobs = self.jobs.list_active_missing_since(company_source_id, previous_success.started_at)
        return self.jobs.deactivate_jobs(missing_jobs)


def company_source_db_to_domain(company_source_db: CompanySourceDB) -> CompanySource:
    return CompanySource(
        company_name=company_source_db.company_name,
        source_name=company_source_db.source.name,
        external_identifier=company_source_db.external_identifier,
        enabled=company_source_db.enabled,
        country=company_source_db.country,
        tags=tuple(company_source_db.tags),
        metadata=company_source_db.metadata_,
    )
