from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorConfigurationError, CollectorHTTPError, CollectorParseError
from radar.collectors.jobs.parsing import normalize_employment_type, normalize_remote_type, parse_datetime, parse_decimal
from radar.http import HTTPClient, HTTPClientError
from radar.models.enums import RemoteType
from radar.models.job import Job
from radar.services.deduplication import generate_fingerprint
from radar.sources.models import CompanySource


class AshbyCollector(BaseCollector[CollectorResult]):
    source_name = "ashby"
    api_url = "https://api.ashbyhq.com/posting-api/job-board/{job_board_name}"

    def __init__(self, company_source: CompanySource, http_client: HTTPClient | None = None) -> None:
        self.company_source = company_source
        self.http_client = http_client or HTTPClient()
        if company_source.source_name != self.source_name:
            raise CollectorConfigurationError("AshbyCollector requires source_name='ashby'")

    def collect(self) -> CollectorResult:
        board_name = self.company_source.external_identifier
        url = self.api_url.format(job_board_name=board_name)
        try:
            payload = self.http_client.get_json(url, params={"includeCompensation": "true"})
        except HTTPClientError as exc:
            raise CollectorHTTPError(str(exc)) from exc

        jobs_payload = _extract_jobs(payload)
        if jobs_payload is None:
            raise CollectorParseError("Ashby payload must contain a jobs list")

        collected_at = datetime.now(timezone.utc)
        jobs = [self._parse_job(item, collected_at) for item in jobs_payload if isinstance(item, dict)]
        return CollectorResult(
            source_name=self.source_name,
            company_source=self.company_source,
            jobs=jobs,
            metadata={"job_board_name": board_name},
        )

    def _parse_job(self, item: dict[str, Any], collected_at: datetime) -> CollectedJob:
        title = item.get("title")
        url = item.get("jobUrl")
        if not title or not url:
            raise CollectorParseError("Ashby job is missing title or jobUrl")

        external_id = _ashby_external_id(item)
        salary_min, salary_max, salary_currency = extract_salary(item.get("compensation"))

        job = Job(
            source=self.source_name,
            external_id=external_id,
            title=str(title),
            company=self.company_source.company_name,
            description=item.get("descriptionPlain"),
            url=str(url),
            location=_location_to_text(item.get("location")),
            remote_type=map_ashby_remote_type(item.get("workplaceType"), item.get("isRemote")),
            employment_type=normalize_employment_type(item.get("employmentType")),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            published_at=parse_datetime(item.get("publishedAt")),
            collected_at=collected_at,
            technologies=[],
            metadata={
                "apply_url": item.get("applyUrl"),
                "department": item.get("department"),
                "team": item.get("team"),
                "secondary_locations": item.get("secondaryLocations"),
                "compensation": item.get("compensation"),
            },
        )
        return CollectedJob(job=job, raw_data=item)


def _extract_jobs(payload: Any) -> list[dict[str, Any]] | None:
    if isinstance(payload, dict):
        jobs = payload.get("jobs")
        return jobs if isinstance(jobs, list) else None
    if isinstance(payload, list):
        return payload
    return None


def _ashby_external_id(item: dict[str, Any]) -> str:
    for key in ("id", "jobId", "jobPostingId"):
        if item.get(key):
            return str(item[key])
    url = str(item.get("jobUrl", ""))
    return generate_fingerprint(source="ashby", url=url, title=item.get("title"))


def map_ashby_remote_type(workplace_type: str | None, is_remote: bool | None) -> RemoteType:
    if is_remote is True:
        return RemoteType.REMOTE
    mapped = normalize_remote_type(workplace_type)
    if mapped is not RemoteType.UNKNOWN:
        return mapped
    if is_remote is False:
        return RemoteType.ONSITE
    return RemoteType.UNKNOWN


def extract_salary(compensation: Any) -> tuple[Decimal | None, Decimal | None, str | None]:
    entries = compensation if isinstance(compensation, list) else [compensation]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        comp_type = str(entry.get("type") or entry.get("compensationType") or "").lower()
        if comp_type and comp_type != "salary":
            continue
        salary_min = parse_decimal(entry.get("min") or entry.get("minimum"))
        salary_max = parse_decimal(entry.get("max") or entry.get("maximum"))
        currency = entry.get("currency")
        if salary_min is not None or salary_max is not None:
            return salary_min, salary_max, currency
    return None, None, None


def _location_to_text(location: Any) -> str | None:
    if isinstance(location, str):
        return location
    if isinstance(location, dict):
        return location.get("name") or location.get("location")
    return None

