import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from radar.collectors.errors import CollectorHTTPError, CollectorParseError
from radar.collectors.jobs.ashby import AshbyCollector, extract_salary, map_ashby_remote_type
from radar.collectors.jobs.greenhouse import GreenhouseCollector
from radar.collectors.jobs.lever import LeverCollector
from radar.collectors.jobs.parsing import normalize_employment_type, normalize_remote_type
from radar.collectors.jobs.smartrecruiters import (
    SmartRecruitersCollector,
    format_smartrecruiters_location,
    map_smartrecruiters_remote_type,
)
from radar.collectors.jobs.workable import WorkableCollector, format_workable_location, map_workable_remote_type
from radar.http import HTTPClientError
from radar.models import EmploymentType, RemoteType
from radar.sources.models import CompanySource


FIXTURES = Path(__file__).parent / "fixtures" / "collectors"


class FakeHTTPClient:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append((url, params, headers))
        if self.error:
            raise self.error
        return self.payload


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_greenhouse_collector_maps_payload_to_job():
    company_source = CompanySource("Example", "greenhouse", "example")
    collector = GreenhouseCollector(company_source, FakeHTTPClient(_load("greenhouse_jobs.json")))

    result = collector.collect()
    job = result.jobs[0].job

    assert result.items_found == 1
    assert job.source == "greenhouse"
    assert job.external_id == "123"
    assert job.company == "Example"
    assert job.title == "Software Engineer"
    assert job.description == "Build APIs & internal tools."
    assert job.url == "https://example.com/greenhouse/software-engineer"
    assert job.location == "Remote"
    assert result.jobs[0].raw_data["id"] == 123


def test_greenhouse_collector_rejects_unexpected_json():
    collector = GreenhouseCollector(CompanySource("Example", "greenhouse", "example"), FakeHTTPClient({"items": []}))

    with pytest.raises(CollectorParseError):
        collector.collect()


def test_lever_collector_maps_payload_to_job():
    collector = LeverCollector(CompanySource("Example", "lever", "example"), FakeHTTPClient(_load("lever_postings.json")))

    result = collector.collect()
    job = result.jobs[0].job

    assert job.source == "lever"
    assert job.external_id == "lever-1"
    assert job.company == "Example"
    assert job.title == "Data Engineer"
    assert job.remote_type is RemoteType.REMOTE
    assert job.employment_type is EmploymentType.FULL_TIME
    assert job.salary_min == Decimal("100000")
    assert job.salary_max == Decimal("140000")
    assert job.salary_currency == "USD"
    assert job.published_at is not None
    assert job.metadata["team"] == "Data"


def test_lever_mapping_helpers_are_conservative():
    assert normalize_remote_type("on-site") is RemoteType.ONSITE
    assert normalize_remote_type("Hybrid") is RemoteType.HYBRID
    assert normalize_remote_type("something else") is RemoteType.UNKNOWN
    assert normalize_employment_type("internship") is EmploymentType.INTERNSHIP
    assert normalize_employment_type("contractor") is EmploymentType.CONTRACT
    assert normalize_employment_type("mystery") is EmploymentType.UNKNOWN


def test_ashby_collector_maps_payload_to_job_and_salary_only():
    collector = AshbyCollector(CompanySource("Example", "ashby", "example"), FakeHTTPClient(_load("ashby_jobs.json")))

    result = collector.collect()
    job = result.jobs[0].job

    assert job.source == "ashby"
    assert job.external_id == "ashby-1"
    assert job.company == "Example"
    assert job.title == "Machine Learning Engineer"
    assert job.remote_type is RemoteType.REMOTE
    assert job.employment_type is EmploymentType.FULL_TIME
    assert job.salary_min == Decimal("120000")
    assert job.salary_max == Decimal("180000")
    assert job.salary_currency == "USD"
    assert job.published_at is not None
    assert job.metadata["team"] == "Applied AI"


def test_ashby_mapping_helpers_are_testable():
    assert map_ashby_remote_type(None, True) is RemoteType.REMOTE
    assert map_ashby_remote_type("Hybrid", None) is RemoteType.HYBRID
    assert map_ashby_remote_type(None, False) is RemoteType.ONSITE
    assert extract_salary([{"type": "Equity", "min": 1}, {"type": "Salary", "min": "10", "max": "20", "currency": "USD"}]) == (
        Decimal("10"),
        Decimal("20"),
        "USD",
    )


def test_collectors_wrap_http_errors():
    collector = LeverCollector(
        CompanySource("Example", "lever", "example"),
        FakeHTTPClient(error=HTTPClientError("boom")),
    )

    with pytest.raises(CollectorHTTPError):
        collector.collect()


def test_workable_collector_maps_public_account_payload():
    http = FakeHTTPClient(_load("workable_jobs.json"))
    collector = WorkableCollector(CompanySource("Example", "workable", "example"), http)

    result = collector.collect()
    remote, hybrid, onsite = [collected.job for collected in result.jobs]

    assert result.items_found == 3
    assert result.metadata == {"subdomain": "example", "account_name": "Example Company"}
    assert http.calls == [("https://www.workable.com/api/accounts/example", {"details": "true"}, None)]
    assert remote.external_id == "ABC123"
    assert remote.title == "Backend Engineer"
    assert remote.company == "Example"
    assert remote.description == "Build Python APIs."
    assert remote.location == "Goiânia, GO, Brazil"
    assert remote.remote_type is RemoteType.REMOTE
    assert remote.employment_type is EmploymentType.FULL_TIME
    assert remote.published_at is not None
    assert remote.metadata["experience"] == "Entry level"
    assert remote.metadata["function"] == "Engineering"
    assert remote.metadata["department"] == "Platform"
    assert remote.metadata["application_url"].endswith("/apply")
    assert result.jobs[0].raw_data["shortcode"] == "ABC123"
    assert hybrid.remote_type is RemoteType.HYBRID
    assert hybrid.employment_type is EmploymentType.INTERNSHIP
    assert onsite.remote_type is RemoteType.ONSITE
    assert onsite.description is None
    assert onsite.location == "GO, Brazil"
    assert onsite.employment_type is EmploymentType.UNKNOWN
    assert onsite.metadata["experience"] is None


def test_workable_remote_mapping_is_conservative():
    assert map_workable_remote_type("remote", False) is RemoteType.REMOTE
    assert map_workable_remote_type("hybrid", True) is RemoteType.HYBRID
    assert map_workable_remote_type("on_site", True) is RemoteType.ONSITE
    assert map_workable_remote_type(None, True) is RemoteType.REMOTE
    assert map_workable_remote_type(None, False) is RemoteType.UNKNOWN


def test_workable_location_uses_structured_fallback():
    assert format_workable_location({"locations": [{"city": "Recife", "region": "PE", "country": "Brazil"}]}) == "Recife, PE, Brazil"
    assert format_workable_location({"country": "Brazil"}) == "Brazil"
    assert format_workable_location({}) is None


def test_workable_collector_deduplicates_repeated_shortcode():
    payload = _load("workable_jobs.json")
    duplicate = dict(payload["jobs"][0], city="Brasília")
    payload["jobs"].append(duplicate)
    collector = WorkableCollector(CompanySource("Example", "workable", "example"), FakeHTTPClient(payload))

    result = collector.collect()

    assert result.items_found == 3
    assert [item.job.external_id for item in result.jobs].count("ABC123") == 1


@pytest.mark.parametrize("payload", [None, [], {}, {"jobs": {}}, {"jobs": "invalid"}])
def test_workable_collector_rejects_invalid_payload(payload):
    collector = WorkableCollector(CompanySource("Example", "workable", "example"), FakeHTTPClient(payload))

    with pytest.raises(CollectorParseError):
        collector.collect()


def test_workable_collector_accepts_empty_public_board_for_lifecycle_guard():
    collector = WorkableCollector(
        CompanySource("Example", "workable", "example"),
        FakeHTTPClient({"name": "Example", "jobs": []}),
    )

    assert collector.collect().items_found == 0


@pytest.mark.parametrize("message", ["timeout", "HTTP 404 for missing tenant", "HTTP 500"])
def test_workable_collector_wraps_http_failures(message):
    collector = WorkableCollector(
        CompanySource("Example", "workable", "missing"),
        FakeHTTPClient(error=HTTPClientError(message)),
    )

    with pytest.raises(CollectorHTTPError, match=message):
        collector.collect()


class SmartRecruitersHTTPClient:
    def __init__(self, list_payloads, details):
        self.list_payloads = list_payloads
        self.details = details
        self.calls = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append((url, params, headers))
        if url.endswith("/postings"):
            return self.list_payloads[params["offset"]]
        return self.details[url.rsplit("/", 1)[-1]]


def _smartrecruiters_collector(http, metadata=None):
    return SmartRecruitersCollector(
        CompanySource("Example", "smartrecruiters", "Example", metadata=metadata or {}),
        http,
        request_interval_seconds=0,
    )


def test_smartrecruiters_collector_maps_listing_and_details():
    listing = _load("smartrecruiters_postings.json")
    details = {item["id"]: item for item in _load("smartrecruiters_details.json")}
    http = SmartRecruitersHTTPClient({0: listing}, details)

    result = _smartrecruiters_collector(http).collect()
    remote, hybrid, onsite = [item.job for item in result.jobs]

    assert result.items_found == 3
    assert result.metadata["complete_snapshot"] is True
    assert result.metadata["collection_mode"] == "full"
    assert result.metadata["requests"] == 4
    assert http.calls[0][1] == {
        "destination": "PUBLIC",
        "limit": 100,
        "offset": 0,
        "country": "br",
    }
    assert remote.external_id == "uuid-1"
    assert remote.title == "Backend Developer Junior"
    assert remote.company == "Example Brazil"
    assert remote.location == "São Carlos, SP, Brazil"
    assert remote.remote_type is RemoteType.REMOTE
    assert remote.employment_type is EmploymentType.FULL_TIME
    assert remote.published_at is not None
    assert remote.url.endswith("backend-developer-junior")
    assert "Descrição da vaga\nConstrua APIs em Python." in remote.description
    assert "Qualificações\n0-1 anos de experiência" in remote.description
    assert "Informações adicionais\nMentoria disponível." in remote.description
    assert remote.metadata["application_url"].endswith("?oga=true")
    assert remote.metadata["experience"] == "Entry Level"
    assert remote.metadata["job_id"] == "job-1"
    assert remote.metadata["job_ad_id"] == "ad-1"
    assert result.jobs[0].raw_data["uuid"] == "uuid-1"
    assert hybrid.remote_type is RemoteType.HYBRID
    assert hybrid.employment_type is EmploymentType.INTERNSHIP
    assert onsite.remote_type is RemoteType.ONSITE
    assert onsite.description is None


def test_smartrecruiters_location_and_modality_are_conservative():
    assert format_smartrecruiters_location({"city": "Goiânia", "country": "br"}) == "Goiânia, Brazil"
    assert format_smartrecruiters_location({"region": "SP"}) == "SP"
    assert format_smartrecruiters_location(None) is None
    assert map_smartrecruiters_remote_type({"remote": True}) is RemoteType.REMOTE
    assert map_smartrecruiters_remote_type({"remote": False, "hybrid": True}) is RemoteType.HYBRID
    assert map_smartrecruiters_remote_type({"locationType": "ONSITE"}) is RemoteType.ONSITE
    assert map_smartrecruiters_remote_type(
        {"remote": False, "hybrid": False, "city": "Campinas"}
    ) is RemoteType.ONSITE
    assert map_smartrecruiters_remote_type({"remote": False}) is RemoteType.UNKNOWN


def test_smartrecruiters_collector_paginates_more_than_one_hundred_and_deduplicates():
    first = [{"id": f"posting-{index}", "uuid": f"uuid-{index}"} for index in range(100)]
    second = [{"id": "posting-100", "uuid": "uuid-100"}, first[0]]
    details = {
        item["id"]: {
            **item,
            "name": f"Job {item['id']}",
            "postingUrl": f"https://jobs.smartrecruiters.com/Example/{item['id']}",
            "active": True,
        }
        for item in first + second
    }
    http = SmartRecruitersHTTPClient(
        {
            0: {"totalFound": 102, "content": first},
            100: {"totalFound": 102, "content": second},
        },
        details,
    )

    result = _smartrecruiters_collector(http).collect()

    assert result.items_found == 101
    assert len({item.job.external_id for item in result.jobs}) == 101
    listing_calls = [call for call in http.calls if call[0].endswith("/postings")]
    assert [call[1]["offset"] for call in listing_calls] == [0, 100]


def test_smartrecruiters_incremental_uses_released_after_and_is_not_complete():
    details = {item["id"]: item for item in _load("smartrecruiters_details.json")}
    http = SmartRecruitersHTTPClient(
        {0: {"totalFound": 1, "content": [{"id": "posting-1", "uuid": "uuid-1"}]}},
        details,
    )
    metadata = {
        "_last_full_reconciliation_at": "2026-08-20T10:00:00+00:00",
        "_last_successful_collection_at": "2026-08-20T11:00:00+00:00",
    }
    collector = SmartRecruitersCollector(
        CompanySource("Example", "smartrecruiters", "Example", metadata=metadata),
        http,
        request_interval_seconds=0,
        now=lambda: datetime(2026, 8, 20, 12, tzinfo=timezone.utc),
    )

    result = collector.collect()

    assert result.metadata["collection_mode"] == "incremental"
    assert result.metadata["complete_snapshot"] is False
    assert http.calls[0][1]["releasedAfter"] == "2026-08-20T10:55:00+00:00"


def test_smartrecruiters_reconciles_after_configured_interval():
    http = SmartRecruitersHTTPClient({0: {"totalFound": 0, "content": []}}, {})
    metadata = {
        "_last_full_reconciliation_at": "2026-08-19T11:00:00+00:00",
        "_last_successful_collection_at": "2026-08-20T11:00:00+00:00",
        "reconciliation_interval_hours": 24,
    }
    collector = SmartRecruitersCollector(
        CompanySource("Example", "smartrecruiters", "Example", metadata=metadata),
        http,
        request_interval_seconds=0,
        now=lambda: datetime(2026, 8, 20, 12, tzinfo=timezone.utc),
    )

    result = collector.collect()

    assert result.items_found == 0
    assert result.metadata["collection_mode"] == "full"
    assert result.metadata["complete_snapshot"] is True
    assert "releasedAfter" not in http.calls[0][1]


@pytest.mark.parametrize("payload", [None, [], {}, {"content": []}, {"totalFound": 1, "content": {}}])
def test_smartrecruiters_collector_rejects_invalid_list_payload(payload):
    collector = _smartrecruiters_collector(FakeHTTPClient(payload))

    with pytest.raises(CollectorParseError):
        collector.collect()


def test_smartrecruiters_collector_rejects_incomplete_pagination():
    collector = _smartrecruiters_collector(
        SmartRecruitersHTTPClient({0: {"totalFound": 1, "content": []}}, {})
    )

    with pytest.raises(CollectorParseError, match="pagination ended"):
        collector.collect()


def test_smartrecruiters_collector_rejects_invalid_detail_payload():
    http = SmartRecruitersHTTPClient(
        {0: {"totalFound": 1, "content": [{"id": "posting-1"}]}},
        {"posting-1": []},
    )

    with pytest.raises(CollectorParseError, match="detail must be an object"):
        _smartrecruiters_collector(http).collect()


@pytest.mark.parametrize(
    "message",
    ["timeout", "HTTP 404 for missing tenant", "HTTP 429", "HTTP 500"],
)
def test_smartrecruiters_collector_wraps_http_failures(message):
    collector = _smartrecruiters_collector(
        FakeHTTPClient(error=HTTPClientError(message))
    )

    with pytest.raises(CollectorHTTPError, match=message):
        collector.collect()
