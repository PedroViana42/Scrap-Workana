from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import os

from sqlalchemy.orm import Session

from radar.collectors.registry import CollectorRegistry
from radar.database.models.company_source import CompanySourceDB
from radar.database.repositories.company_sources import CompanySourceRepository
from radar.database.repositories.mappers import company_source_db_to_domain
from radar.database.repositories.scrape_runs import ScrapeRunRepository
from radar.services.job_collection import JobCollectionService, JobCollectionSummary


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DueCompanySource:
    company_source: CompanySourceDB
    interval_minutes: int
    last_finished_at: datetime | None
    due_at: datetime | None
    overdue_seconds: int


@dataclass(frozen=True)
class SchedulerCycleResult:
    due_count: int
    would_process: int
    processed: list[JobCollectionSummary]
    dry_run: bool = False
    due: list[DueCompanySource] | None = None


def scheduler_batch_size() -> int:
    return int(os.getenv("RADAR_SCHEDULER_BATCH_SIZE", "5"))


def scheduler_poll_seconds() -> int:
    return int(os.getenv("RADAR_SCHEDULER_POLL_SECONDS", "60"))


def company_interval_minutes(company_source: CompanySourceDB) -> int:
    override = (company_source.metadata_ or {}).get("interval_minutes")
    if override is not None:
        return max(1, int(override))
    return max(1, int(company_source.source.interval_minutes or 60))


def list_due_company_sources(session: Session, now: datetime | None = None) -> list[DueCompanySource]:
    now = now or datetime.now(timezone.utc)
    scrape_runs = ScrapeRunRepository(session)
    due: list[DueCompanySource] = []
    for company_source in CompanySourceRepository(session).list_enabled_with_enabled_sources():
        interval = company_interval_minutes(company_source)
        last_run = scrape_runs.get_last_run(company_source.id)
        if last_run is None or last_run.finished_at is None:
            due.append(
                DueCompanySource(
                    company_source=company_source,
                    interval_minutes=interval,
                    last_finished_at=None,
                    due_at=None,
                    overdue_seconds=2_147_483_647 - int(company_source.id),
                )
            )
            continue
        due_at = last_run.finished_at + timedelta(minutes=interval)
        if now >= due_at:
            due.append(
                DueCompanySource(
                    company_source=company_source,
                    interval_minutes=interval,
                    last_finished_at=last_run.finished_at,
                    due_at=due_at,
                    overdue_seconds=int((now - due_at).total_seconds()),
                )
            )
    return sorted(due, key=lambda item: (-item.overdue_seconds, item.company_source.id))


def run_scheduler_cycle(
    session: Session,
    *,
    dry_run: bool = False,
    batch_size: int | None = None,
    max_companies: int | None = None,
    registry: CollectorRegistry | None = None,
) -> SchedulerCycleResult:
    limit = max_companies if max_companies is not None else (batch_size or scheduler_batch_size())
    due = list_due_company_sources(session)
    selected = due[:limit]

    logger.info(
        "scheduler_cycle_started due=%s would_process=%s dry_run=%s",
        len(due),
        len(selected),
        dry_run,
    )

    if dry_run:
        return SchedulerCycleResult(due_count=len(due), would_process=len(selected), processed=[], dry_run=True, due=selected)

    processed: list[JobCollectionSummary] = []
    for item in selected:
        company_source = item.company_source
        started_at = datetime.now(timezone.utc)
        logger.info(
            "company_collection_started source=%s company_source_id=%s company=%s",
            company_source.source.name,
            company_source.id,
            company_source.company_name,
        )
        try:
            summary = JobCollectionService(session, registry=registry).collect_and_persist(
                company_source_db_to_domain(company_source),
                persist_company_source=False,
            )
            processed.append(summary)
            duration = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
            logger.info(
                "company_collection_finished source=%s company_source_id=%s company=%s duration_ms=%s "
                "items_found=%s items_new=%s items_updated=%s items_deactivated=%s status=%s",
                company_source.source.name,
                company_source.id,
                company_source.company_name,
                duration,
                summary.items_found,
                summary.items_new,
                summary.items_updated,
                summary.items_deactivated,
                summary.status.value,
            )
        except Exception:
            logger.exception(
                "company_collection_failed source=%s company_source_id=%s company=%s",
                company_source.source.name,
                company_source.id,
                company_source.company_name,
            )
            session.rollback()
    return SchedulerCycleResult(due_count=len(due), would_process=len(selected), processed=processed, dry_run=False, due=selected)
