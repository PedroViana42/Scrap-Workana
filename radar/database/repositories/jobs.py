from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from radar.database.models.job import JobDB
from radar.database.repositories.mappers import job_to_values
from radar.database.repositories.sources import SourceRepository
from radar.models.job import Job
from radar.relevance.models import RelevanceResult
from radar.services.deduplication import job_fingerprint


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.sources = SourceRepository(session)

    def get_by_fingerprint(self, fingerprint: str) -> JobDB | None:
        return self.session.scalar(select(JobDB).where(JobDB.fingerprint == fingerprint))

    def get_by_external_id(self, source_id: int, external_id: str | None) -> JobDB | None:
        if not external_id:
            return None
        return self.session.scalar(
            select(JobDB).where(JobDB.source_id == source_id, JobDB.external_id == external_id)
        )

    def upsert(self, job: Job, company_source_id: int | None = None, raw_data: dict | None = None) -> tuple[JobDB, bool]:
        source = self.sources.get_by_name(job.source)
        if source is None:
            raise ValueError(f"Source not found for job: {job.source}")

        fingerprint = job_fingerprint(job)
        existing = self.get_by_external_id(source.id, job.external_id) or self.get_by_fingerprint(fingerprint)
        values = job_to_values(job, source.id, fingerprint, company_source_id)
        if raw_data is not None:
            values["raw_data"] = raw_data

        if existing is None:
            values["first_seen_at"] = job.collected_at
            existing = JobDB(**values)
            self.session.add(existing)
            self.session.flush()
            return existing, True

        for field, value in values.items():
            if field == "first_seen_at":
                continue
            setattr(existing, field, value)
        existing.active = True
        existing.deactivated_at = None
        self.session.flush()
        return existing, False

    def update_relevance(self, job_id: int, result: RelevanceResult, technologies: list[str] | None = None) -> JobDB:
        job = self.session.get(JobDB, job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        job.relevance_score = result.score
        job.relevance_band = result.band.value
        job.relevance_reasons = result.reasons_payload()
        job.relevance_components = result.components
        job.relevance_version = result.version
        job.scored_at = datetime.now(timezone.utc)
        if technologies is not None:
            job.technologies = sorted(set(technologies))
        self.session.flush()
        return job

    def list_for_rescore(self, limit: int | None = None) -> list[JobDB]:
        statement = select(JobDB).where(JobDB.active.is_(True)).order_by(JobDB.id)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement))

    def list_active_by_relevance(self, limit: int = 20) -> list[JobDB]:
        return list(
            self.session.scalars(
                select(JobDB)
                .where(JobDB.active.is_(True))
                .order_by(JobDB.relevance_score.desc().nullslast(), JobDB.id)
                .limit(limit)
            )
        )

    def count_active_by_company_source(self, company_source_id: int) -> int:
        from sqlalchemy import func

        return int(
            self.session.scalar(
                select(func.count()).select_from(JobDB).where(
                    JobDB.company_source_id == company_source_id,
                    JobDB.active.is_(True),
                )
            )
            or 0
        )

    def list_active_missing_since(self, company_source_id: int, cutoff_started_at: datetime) -> list[JobDB]:
        return list(
            self.session.scalars(
                select(JobDB).where(
                    JobDB.company_source_id == company_source_id,
                    JobDB.active.is_(True),
                    JobDB.last_seen_at < cutoff_started_at,
                )
            )
        )

    def deactivate_jobs(self, jobs: list[JobDB], deactivated_at: datetime | None = None) -> int:
        timestamp = deactivated_at or datetime.now(timezone.utc)
        for job in jobs:
            job.active = False
            job.deactivated_at = timestamp
        self.session.flush()
        return len(jobs)
