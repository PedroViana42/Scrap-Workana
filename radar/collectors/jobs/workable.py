from datetime import datetime, timezone
from typing import Any

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorConfigurationError, CollectorHTTPError, CollectorParseError
from radar.collectors.jobs.parsing import html_to_text, normalize_employment_type, normalize_remote_type, parse_datetime
from radar.http import HTTPClient, HTTPClientError
from radar.models.enums import RemoteType
from radar.models.job import Job
from radar.sources.models import CompanySource


class WorkableCollector(BaseCollector[CollectorResult]):
    source_name = "workable"
    api_url = "https://www.workable.com/api/accounts/{subdomain}"

    def __init__(self, company_source: CompanySource, http_client: HTTPClient | None = None) -> None:
        self.company_source = company_source
        self.http_client = http_client or HTTPClient()
        if company_source.source_name != self.source_name:
            raise CollectorConfigurationError("WorkableCollector requires source_name='workable'")

    def collect(self) -> CollectorResult:
        subdomain = self.company_source.external_identifier
        try:
            payload = self.http_client.get_json(
                self.api_url.format(subdomain=subdomain),
                params={"details": "true"},
            )
        except HTTPClientError as exc:
            raise CollectorHTTPError(str(exc)) from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise CollectorParseError("Workable payload must contain a jobs list")

        collected_at = datetime.now(timezone.utc)
        jobs_by_external_id: dict[str, CollectedJob] = {}
        for item in payload["jobs"]:
            if not isinstance(item, dict):
                continue
            collected_job = self._parse_job(item, collected_at)
            jobs_by_external_id.setdefault(str(collected_job.job.external_id), collected_job)
        jobs = list(jobs_by_external_id.values())
        return CollectorResult(
            source_name=self.source_name,
            company_source=self.company_source,
            jobs=jobs,
            metadata={"subdomain": subdomain, "account_name": payload.get("name")},
        )

    def _parse_job(self, item: dict[str, Any], collected_at: datetime) -> CollectedJob:
        external_id = item.get("shortcode") or item.get("id") or item.get("code")
        title = item.get("title")
        url = item.get("url") or item.get("shortlink") or item.get("application_url")
        if not external_id or not title or not url:
            raise CollectorParseError("Workable job is missing shortcode, title, or URL")

        job = Job(
            source=self.source_name,
            external_id=str(external_id),
            title=str(title),
            company=self.company_source.company_name,
            description=html_to_text(item.get("description")),
            url=str(url),
            location=format_workable_location(item),
            remote_type=map_workable_remote_type(item.get("workplace_type"), item.get("telecommuting")),
            employment_type=normalize_employment_type(item.get("employment_type")),
            published_at=parse_datetime(item.get("published_on") or item.get("created_at")),
            collected_at=collected_at,
            technologies=[],
            metadata={
                "application_url": item.get("application_url"),
                "shortlink": item.get("shortlink"),
                "shortcode": item.get("shortcode"),
                "code": item.get("code"),
                "workplace_type": item.get("workplace_type"),
                "telecommuting": item.get("telecommuting"),
                "experience": item.get("experience"),
                "function": item.get("function"),
                "department": item.get("department"),
                "education": item.get("education"),
                "industry": item.get("industry"),
                "locations": item.get("locations"),
                "created_at": item.get("created_at"),
            },
        )
        return CollectedJob(job=job, raw_data=item)


def map_workable_remote_type(workplace_type: Any, telecommuting: Any) -> RemoteType:
    normalized_workplace = workplace_type.replace("_", "-") if isinstance(workplace_type, str) else None
    mapped = normalize_remote_type(normalized_workplace)
    if mapped is not RemoteType.UNKNOWN:
        return mapped
    if telecommuting is True:
        return RemoteType.REMOTE
    return RemoteType.UNKNOWN


def format_workable_location(item: dict[str, Any]) -> str | None:
    locations = item.get("locations")
    if isinstance(locations, list):
        formatted_locations: list[str] = []
        for location in locations:
            if isinstance(location, dict) and location.get("hidden") is not True:
                parts = _location_parts(location)
                if parts:
                    formatted = ", ".join(parts)
                    if formatted not in formatted_locations:
                        formatted_locations.append(formatted)
        if formatted_locations:
            return "; ".join(formatted_locations)

    primary = _location_parts(item)
    if primary:
        return ", ".join(primary)
    return None


def _location_parts(value: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for key in ("city", "state", "region", "country"):
        part = value.get(key)
        if isinstance(part, str) and part.strip() and part.strip() not in parts:
            parts.append(part.strip())
    return parts
