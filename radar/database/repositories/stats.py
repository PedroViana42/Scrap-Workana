from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from radar.database.models.company_source import CompanySourceDB
from radar.database.models.job import JobDB
from radar.database.models.scrape_run import ScrapeRunDB
from radar.database.models.source import SourceDB


class StatsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def summary(self) -> dict:
        return {
            "jobs_total": self._count(select(func.count()).select_from(JobDB)),
            "jobs_active": self._count(select(func.count()).select_from(JobDB).where(JobDB.active.is_(True))),
            "sources_total": self._count(select(func.count()).select_from(SourceDB)),
            "sources_enabled": self._count(select(func.count()).select_from(SourceDB).where(SourceDB.enabled.is_(True))),
            "company_sources_enabled": self._count(
                select(func.count()).select_from(CompanySourceDB).where(CompanySourceDB.enabled.is_(True))
            ),
            "jobs_by_relevance_band": self.jobs_by_relevance_band(),
            "scrape_runs_24h": self.scrape_runs_24h(),
            "last_successful_scrape": self.session.scalar(
                select(func.max(ScrapeRunDB.finished_at)).where(ScrapeRunDB.status == "success")
            ),
        }

    def jobs_by_relevance_band(self) -> dict[str, int]:
        expected = {"excellent": 0, "strong": 0, "interesting": 0, "low": 0, "very_low": 0}
        rows = self.session.execute(
            select(JobDB.relevance_band, func.count())
            .where(JobDB.active.is_(True), JobDB.relevance_band.is_not(None))
            .group_by(JobDB.relevance_band)
        )
        for band, count in rows:
            expected[str(band)] = int(count)
        return expected

    def scrape_runs_24h(self) -> dict[str, int]:
        expected = {"success": 0, "partial": 0, "failed": 0}
        rows = self.session.execute(
            text(
                """
                select status, count(*)
                from scrape_runs
                where started_at >= now() - interval '24 hours'
                group by status
                """
            )
        )
        for status, count in rows:
            if status in expected:
                expected[status] = int(count)
        return expected

    def _count(self, statement) -> int:
        return int(self.session.scalar(statement) or 0)
