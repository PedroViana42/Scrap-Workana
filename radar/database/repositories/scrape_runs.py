from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from radar.database.models.scrape_run import ScrapeRunDB


class ScrapeRunStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ScrapeRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def start(self, source_id: int, company_source_id: int | None = None, metadata: dict | None = None) -> ScrapeRunDB:
        run = ScrapeRunDB(
            source_id=source_id,
            company_source_id=company_source_id,
            status=ScrapeRunStatus.RUNNING.value,
            metadata_=metadata or {},
        )
        self.session.add(run)
        self.session.flush()
        return run

    def finish(
        self,
        run: ScrapeRunDB,
        status: ScrapeRunStatus,
        items_found: int = 0,
        items_new: int = 0,
        items_updated: int = 0,
        items_deactivated: int = 0,
        error_type: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> ScrapeRunDB:
        finished_at = datetime.now(timezone.utc)
        run.finished_at = finished_at
        run.status = status.value
        run.items_found = items_found
        run.items_new = items_new
        run.items_updated = items_updated
        run.items_deactivated = items_deactivated
        run.error_type = error_type
        run.error_message = error_message
        if metadata is not None:
            run.metadata_ = metadata
        if run.started_at:
            run.duration_ms = int((finished_at - run.started_at).total_seconds() * 1000)
        self.session.flush()
        return run

    def get_last_run(self, company_source_id: int) -> ScrapeRunDB | None:
        return self.session.scalar(
            select(ScrapeRunDB)
            .where(
                ScrapeRunDB.company_source_id == company_source_id,
                ScrapeRunDB.finished_at.is_not(None),
            )
            .order_by(ScrapeRunDB.finished_at.desc(), ScrapeRunDB.id.desc())
            .limit(1)
        )

    def get_last_successful_run(self, company_source_id: int) -> ScrapeRunDB | None:
        return self.session.scalar(
            select(ScrapeRunDB)
            .where(
                ScrapeRunDB.company_source_id == company_source_id,
                ScrapeRunDB.status == ScrapeRunStatus.SUCCESS.value,
                ScrapeRunDB.finished_at.is_not(None),
            )
            .order_by(ScrapeRunDB.finished_at.desc(), ScrapeRunDB.id.desc())
            .limit(1)
        )

    def list_recent(
        self,
        company_source_id: int | None = None,
        status: ScrapeRunStatus | None = None,
        limit: int = 50,
    ) -> list[ScrapeRunDB]:
        statement = select(ScrapeRunDB).where(ScrapeRunDB.finished_at.is_not(None))
        if company_source_id is not None:
            statement = statement.where(ScrapeRunDB.company_source_id == company_source_id)
        if status is not None:
            statement = statement.where(ScrapeRunDB.status == status.value)
        return list(self.session.scalars(statement.order_by(ScrapeRunDB.finished_at.desc(), ScrapeRunDB.id.desc()).limit(limit)))

    def list_successful_before(self, company_source_id: int, before_run_id: int, limit: int = 2) -> list[ScrapeRunDB]:
        before_run = self.session.get(ScrapeRunDB, before_run_id)
        if before_run is None:
            return []
        return list(
            self.session.scalars(
                select(ScrapeRunDB)
                .where(
                    ScrapeRunDB.company_source_id == company_source_id,
                    ScrapeRunDB.status == ScrapeRunStatus.SUCCESS.value,
                    ScrapeRunDB.finished_at.is_not(None),
                    ScrapeRunDB.started_at <= before_run.started_at,
                )
                .order_by(ScrapeRunDB.started_at.desc(), ScrapeRunDB.id.desc())
                .limit(limit)
            )
        )
