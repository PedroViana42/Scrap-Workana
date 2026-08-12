import json
from decimal import Decimal
from pathlib import Path

import pytest

from radar.collectors.errors import CollectorHTTPError, CollectorParseError
from radar.collectors.jobs.ashby import AshbyCollector, extract_salary, map_ashby_remote_type
from radar.collectors.jobs.greenhouse import GreenhouseCollector
from radar.collectors.jobs.lever import LeverCollector
from radar.collectors.jobs.parsing import normalize_employment_type, normalize_remote_type
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

