from datetime import datetime

from pydantic import BaseModel


class StatsResponse(BaseModel):
    jobs_total: int
    jobs_active: int
    sources_total: int
    sources_enabled: int
    company_sources_enabled: int
    jobs_by_relevance_band: dict[str, int]
    scrape_runs_24h: dict[str, int]
    last_successful_scrape: datetime | None
