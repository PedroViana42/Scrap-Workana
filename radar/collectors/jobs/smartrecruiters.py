from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from typing import Any, Callable

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import (
    CollectorConfigurationError,
    CollectorHTTPError,
    CollectorParseError,
)
from radar.collectors.jobs.parsing import (
    html_to_text,
    normalize_employment_type,
    parse_datetime,
)
from radar.http import HTTPClient, HTTPClientError
from radar.models.enums import RemoteType
from radar.models.job import Job
from radar.sources.models import CompanySource


class SmartRecruitersCollector(BaseCollector[CollectorResult]):
    source_name = "smartrecruiters"
    api_url = "https://api.smartrecruiters.com/v1/companies/{company_identifier}/postings"
    page_size = 100
    supports_incremental_collection = True

    def __init__(
        self,
        company_source: CompanySource,
        http_client: HTTPClient | None = None,
        *,
        request_interval_seconds: float = 0.11,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.company_source = company_source
        self.http_client = http_client or HTTPClient(timeout=128)
        self.request_interval_seconds = max(0.0, request_interval_seconds)
        self.sleep = sleep
        self.monotonic = monotonic
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._last_request_at: float | None = None
        self.requests_made = 0
        if company_source.source_name != self.source_name:
            raise CollectorConfigurationError(
                "SmartRecruitersCollector requires source_name='smartrecruiters'"
            )

    def collect(self) -> CollectorResult:
        started_at = self.now()
        mode, released_after = self._collection_mode(started_at)
        posting_summaries = self._list_postings(released_after=released_after)
        collected_at = self.now()
        jobs_by_external_id: dict[str, CollectedJob] = {}
        for summary in posting_summaries:
            posting_id = summary.get("id") or summary.get("uuid")
            if not posting_id:
                raise CollectorParseError("SmartRecruiters posting summary is missing id and uuid")
            detail = self._get_posting_detail(str(posting_id))
            if detail.get("active") is False:
                continue
            collected_job = self._parse_job(detail, collected_at)
            jobs_by_external_id.setdefault(str(collected_job.job.external_id), collected_job)

        complete_snapshot = mode == "full"
        return CollectorResult(
            source_name=self.source_name,
            company_source=self.company_source,
            jobs=list(jobs_by_external_id.values()),
            metadata={
                "collection_mode": mode,
                "complete_snapshot": complete_snapshot,
                "country": self._country_filter(),
                "released_after": released_after,
                "requests": self.requests_made,
                "collection_started_at": started_at.isoformat(),
            },
        )

    def _collection_mode(self, now: datetime) -> tuple[str, str | None]:
        metadata = self.company_source.metadata
        if metadata.get("force_full_reconciliation") is True:
            return "full", None
        last_full = parse_datetime(metadata.get("_last_full_reconciliation_at"))
        last_success = parse_datetime(metadata.get("_last_successful_collection_at"))
        interval_hours = max(1, int(metadata.get("reconciliation_interval_hours", 24)))
        if last_full is None or now - last_full >= timedelta(hours=interval_hours):
            return "full", None
        if last_success is None:
            return "full", None
        overlap_minutes = max(0, int(metadata.get("incremental_overlap_minutes", 5)))
        released_after = last_success - timedelta(minutes=overlap_minutes)
        return "incremental", released_after.isoformat()

    def _country_filter(self) -> str | None:
        value = self.company_source.metadata.get("country_filter", "br")
        return str(value).lower().strip() if value else None

    def _list_postings(self, released_after: str | None) -> list[dict[str, Any]]:
        url = self.api_url.format(company_identifier=self.company_source.external_identifier)
        offset = 0
        postings: list[dict[str, Any]] = []
        seen: set[str] = set()
        total_found: int | None = None

        while total_found is None or offset < total_found:
            params: dict[str, Any] = {
                "destination": "PUBLIC",
                "limit": self.page_size,
                "offset": offset,
            }
            country = self._country_filter()
            if country:
                params["country"] = country
            if released_after:
                params["releasedAfter"] = released_after
            payload = self._get_json(url, params=params)
            page, total_found = _parse_posting_list(payload)
            if not page:
                if offset < total_found:
                    raise CollectorParseError(
                        "SmartRecruiters pagination ended before totalFound"
                    )
                break
            for posting in page:
                identity = str(posting.get("uuid") or posting.get("id") or "")
                if not identity:
                    raise CollectorParseError(
                        "SmartRecruiters posting summary is missing id and uuid"
                    )
                if identity not in seen:
                    postings.append(posting)
                    seen.add(identity)
            offset += len(page)
        return postings

    def _get_posting_detail(self, posting_id: str) -> dict[str, Any]:
        url = (
            self.api_url.format(company_identifier=self.company_source.external_identifier)
            + f"/{posting_id}"
        )
        payload = self._get_json(url, params={})
        if not isinstance(payload, dict):
            raise CollectorParseError("SmartRecruiters posting detail must be an object")
        return payload

    def _get_json(self, url: str, params: dict[str, Any]) -> Any:
        self._throttle()
        try:
            result = self.http_client.get_json(url, params=params)
        except HTTPClientError as exc:
            raise CollectorHTTPError(str(exc)) from exc
        self.requests_made += 1
        self._last_request_at = self.monotonic()
        return result

    def _throttle(self) -> None:
        if self._last_request_at is None or self.request_interval_seconds == 0:
            return
        remaining = self.request_interval_seconds - (self.monotonic() - self._last_request_at)
        if remaining > 0:
            self.sleep(remaining)

    def _parse_job(self, item: dict[str, Any], collected_at: datetime) -> CollectedJob:
        external_id = item.get("uuid") or item.get("id")
        title = item.get("name")
        url = item.get("postingUrl") or item.get("applyUrl")
        if not external_id or not title or not url:
            raise CollectorParseError(
                "SmartRecruiters posting is missing id/uuid, name, or posting URL"
            )

        company = item.get("company") if isinstance(item.get("company"), dict) else {}
        department = (
            item.get("department") if isinstance(item.get("department"), dict) else {}
        )
        function = item.get("function") if isinstance(item.get("function"), dict) else {}
        experience = (
            item.get("experienceLevel")
            if isinstance(item.get("experienceLevel"), dict)
            else {}
        )
        employment = (
            item.get("typeOfEmployment")
            if isinstance(item.get("typeOfEmployment"), dict)
            else {}
        )
        sections = _job_ad_sections(item)
        description = _format_description(sections)

        job = Job(
            source=self.source_name,
            external_id=str(external_id),
            title=str(title),
            company=str(company.get("name") or self.company_source.company_name),
            description=description,
            url=str(url),
            location=format_smartrecruiters_location(item.get("location")),
            remote_type=map_smartrecruiters_remote_type(item.get("location")),
            employment_type=normalize_employment_type(
                employment.get("label") or employment.get("id")
            ),
            published_at=parse_datetime(item.get("releasedDate")),
            collected_at=collected_at,
            technologies=[],
            metadata={
                "id": item.get("id"),
                "uuid": item.get("uuid"),
                "job_id": item.get("jobId"),
                "job_ad_id": item.get("jobAdId"),
                "ref_number": item.get("refNumber"),
                "company_identifier": company.get("identifier"),
                "department": department,
                "function": function,
                "experience": (
                    experience.get("name")
                    or experience.get("label")
                    or experience.get("id")
                ),
                "experience_level": experience,
                "type_of_employment": employment,
                "posting_url": item.get("postingUrl"),
                "application_url": item.get("applyUrl"),
                "active": item.get("active"),
                "job_ad_sections": sections,
            },
        )
        return CollectedJob(job=job, raw_data=item)


def _parse_posting_list(payload: Any) -> tuple[list[dict[str, Any]], int]:
    if not isinstance(payload, dict):
        raise CollectorParseError("SmartRecruiters posting list must be an object")
    content = payload.get("content")
    total_found = payload.get("totalFound")
    if not isinstance(content, list) or not isinstance(total_found, int) or total_found < 0:
        raise CollectorParseError(
            "SmartRecruiters posting list requires content and totalFound"
        )
    if any(not isinstance(item, dict) for item in content):
        raise CollectorParseError("SmartRecruiters posting list contains an invalid item")
    return content, total_found


def _job_ad_sections(item: dict[str, Any]) -> dict[str, Any]:
    job_ad = item.get("jobAd") if isinstance(item.get("jobAd"), dict) else {}
    sections = job_ad.get("sections") if isinstance(job_ad.get("sections"), dict) else {}
    return sections


def _format_description(sections: dict[str, Any]) -> str | None:
    parts: list[str] = []
    for key in ("jobDescription", "qualifications", "additionalInformation"):
        section = sections.get(key)
        if not isinstance(section, dict):
            continue
        text = html_to_text(section.get("text"))
        if not text:
            continue
        title = html_to_text(section.get("title"))
        parts.append(f"{title}\n{text}" if title else text)
    return "\n\n".join(parts) or None


def map_smartrecruiters_remote_type(location: Any) -> RemoteType:
    if not isinstance(location, dict):
        return RemoteType.UNKNOWN
    location_type = str(location.get("locationType") or "").upper()
    if location_type == "HYBRID":
        return RemoteType.HYBRID
    if location_type == "REMOTE":
        return RemoteType.REMOTE
    if location_type == "ONSITE":
        return RemoteType.ONSITE
    if location.get("hybrid") is True:
        return RemoteType.HYBRID
    if location.get("remote") is True:
        return RemoteType.REMOTE
    has_physical_location = any(location.get(key) for key in ("city", "region", "country"))
    if (
        location.get("remote") is False
        and location.get("hybrid") is False
        and has_physical_location
    ):
        return RemoteType.ONSITE
    return RemoteType.UNKNOWN


def format_smartrecruiters_location(location: Any) -> str | None:
    if not isinstance(location, dict):
        return None
    parts: list[str] = []
    for key in ("city", "region", "country"):
        value = location.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        normalized = _canonical_country(value) if key == "country" else value.strip()
        if normalized not in parts:
            parts.append(normalized)
    return ", ".join(parts) or None


def _canonical_country(value: str) -> str:
    return "Brazil" if value.strip().lower() == "br" else value.strip()
