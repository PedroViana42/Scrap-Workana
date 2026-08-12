from datetime import datetime, timezone
from typing import Any

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorConfigurationError, CollectorHTTPError, CollectorParseError
from radar.collectors.jobs.parsing import html_to_text
from radar.http import HTTPClient, HTTPClientError
from radar.models.job import Job
from radar.sources.models import CompanySource


class GreenhouseCollector(BaseCollector[CollectorResult]):
    source_name = "greenhouse"
    api_url = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    def __init__(self, company_source: CompanySource, http_client: HTTPClient | None = None) -> None:
        self.company_source = company_source
        self.http_client = http_client or HTTPClient()
        if company_source.source_name != self.source_name:
            raise CollectorConfigurationError("GreenhouseCollector requires source_name='greenhouse'")

    def collect(self) -> CollectorResult:
        board_token = self.company_source.external_identifier
        url = self.api_url.format(board_token=board_token)
        try:
            payload = self.http_client.get_json(url, params={"content": "true"})
        except HTTPClientError as exc:
            raise CollectorHTTPError(str(exc)) from exc

        jobs_payload = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs_payload, list):
            raise CollectorParseError("Greenhouse payload must contain a jobs list")

        collected_at = datetime.now(timezone.utc)
        jobs = [self._parse_job(item, collected_at) for item in jobs_payload if isinstance(item, dict)]
        return CollectorResult(
            source_name=self.source_name,
            company_source=self.company_source,
            jobs=jobs,
            metadata={"board_token": board_token},
        )

    def _parse_job(self, item: dict[str, Any], collected_at: datetime) -> CollectedJob:
        external_id = item.get("id")
        title = item.get("title")
        url = item.get("absolute_url")
        if external_id is None or not title or not url:
            raise CollectorParseError("Greenhouse job is missing id, title, or absolute_url")

        location = item.get("location") or {}
        description = html_to_text(item.get("content"))

        job = Job(
            source=self.source_name,
            external_id=str(external_id),
            title=str(title),
            company=self.company_source.company_name,
            description=description,
            url=str(url),
            location=location.get("name") if isinstance(location, dict) else None,
            collected_at=collected_at,
            technologies=[],
            metadata={
                "requisition_id": item.get("requisition_id"),
                "departments": item.get("departments", []),
                "offices": item.get("offices", []),
            },
        )
        return CollectedJob(job=job, raw_data=item)

