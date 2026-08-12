from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorConfigurationError, CollectorHTTPError, CollectorParseError
from radar.collectors.jobs.parsing import normalize_employment_type, normalize_remote_type, parse_datetime, parse_decimal
from radar.http import HTTPClient, HTTPClientError
from radar.models.job import Job
from radar.sources.models import CompanySource


class LeverCollector(BaseCollector[CollectorResult]):
    source_name = "lever"
    api_hosts = {
        "global": "https://api.lever.co/v0/postings/{site}",
        "eu": "https://api.eu.lever.co/v0/postings/{site}",
    }

    def __init__(self, company_source: CompanySource, http_client: HTTPClient | None = None) -> None:
        self.company_source = company_source
        self.http_client = http_client or HTTPClient()
        if company_source.source_name != self.source_name:
            raise CollectorConfigurationError("LeverCollector requires source_name='lever'")

    def collect(self) -> CollectorResult:
        site = self.company_source.external_identifier
        api_region = str(self.company_source.metadata.get("api_region", "global"))
        url_template = self.api_hosts.get(api_region)
        if url_template is None:
            raise CollectorConfigurationError(f"Unsupported Lever api_region: {api_region}")

        try:
            payload = self.http_client.get_json(url_template.format(site=site), params={"mode": "json"})
        except HTTPClientError as exc:
            raise CollectorHTTPError(str(exc)) from exc

        if not isinstance(payload, list):
            raise CollectorParseError("Lever payload must be a list")

        collected_at = datetime.now(timezone.utc)
        jobs = [self._parse_job(item, collected_at) for item in payload if isinstance(item, dict)]
        return CollectorResult(
            source_name=self.source_name,
            company_source=self.company_source,
            jobs=jobs,
            metadata={"site": site, "api_region": api_region},
        )

    def _parse_job(self, item: dict[str, Any], collected_at: datetime) -> CollectedJob:
        external_id = item.get("id")
        title = item.get("text")
        url = item.get("hostedUrl")
        if not external_id or not title or not url:
            raise CollectorParseError("Lever posting is missing id, text, or hostedUrl")

        categories = item.get("categories") or {}
        salary_min, salary_max, salary_currency = _parse_salary_range(item.get("salaryRange"))

        job = Job(
            source=self.source_name,
            external_id=str(external_id),
            title=str(title),
            company=self.company_source.company_name,
            description=item.get("descriptionPlain") or item.get("description"),
            url=str(url),
            location=categories.get("location") if isinstance(categories, dict) else None,
            remote_type=normalize_remote_type(item.get("workplaceType")),
            employment_type=normalize_employment_type(categories.get("commitment") if isinstance(categories, dict) else None),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            published_at=parse_datetime(item.get("createdAt")),
            collected_at=collected_at,
            technologies=[],
            metadata={
                "team": categories.get("team") if isinstance(categories, dict) else None,
                "department": categories.get("department") if isinstance(categories, dict) else None,
                "all_locations": item.get("allLocations"),
                "country": item.get("country"),
                "apply_url": item.get("applyUrl"),
                "workplace_type": item.get("workplaceType"),
            },
        )
        return CollectedJob(job=job, raw_data=item)


def _parse_salary_range(value: dict[str, Any] | None) -> tuple[Decimal | None, Decimal | None, str | None]:
    if not isinstance(value, dict):
        return None, None, None
    return (
        parse_decimal(value.get("min")),
        parse_decimal(value.get("max")),
        value.get("currency"),
    )

