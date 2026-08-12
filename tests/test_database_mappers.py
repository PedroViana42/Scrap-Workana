from datetime import datetime, timezone
from decimal import Decimal

from radar.database.repositories.mappers import deal_to_values, job_to_values, source_config_to_values
from radar.models import Deal, EmploymentType, Job, RemoteType, Seniority
from radar.sources.catalog import get_source


def test_source_config_maps_to_database_values():
    source = get_source("greenhouse")
    values = source_config_to_values(source)

    assert values["name"] == "greenhouse"
    assert values["content_type"] == "job"
    assert values["status"] == "active"
    assert values["enabled"] is True
    assert values["capabilities"]["supports_company_boards"] is True


def test_job_maps_domain_fields_to_database_values():
    collected_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    job = Job(
        source="greenhouse",
        external_id="job-1",
        title="Data Engineer",
        company="Example",
        description="Python and SQL",
        url="https://example.com/jobs/1",
        location="Remote",
        remote_type=RemoteType.REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        seniority=Seniority.SENIOR,
        salary_min=Decimal("10000.00"),
        salary_max=Decimal("14000.00"),
        salary_currency="BRL",
        technologies=["python", "sql"],
        collected_at=collected_at,
        metadata={"department": "data"},
    )

    values = job_to_values(job, source_id=1, fingerprint="abc")

    assert values["source_id"] == 1
    assert values["fingerprint"] == "abc"
    assert values["remote_type"] == "remote"
    assert values["employment_type"] == "full_time"
    assert values["seniority"] == "senior"
    assert values["salary_min"] == Decimal("10000.00")
    assert values["technologies"] == ["python", "sql"]
    assert values["metadata_"] == {"department": "data"}
    assert values["last_seen_at"] == collected_at


def test_deal_maps_domain_fields_to_database_values():
    collected_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    deal = Deal(
        source="amazon",
        external_id="deal-1",
        title="Keyboard",
        description="Mechanical keyboard",
        url="https://example.com/deals/1",
        image_url="https://example.com/image.jpg",
        store="Amazon",
        price=Decimal("299.90"),
        original_price=Decimal("399.90"),
        currency="BRL",
        coupon="RADAR10",
        collected_at=collected_at,
        metadata={"category": "peripherals"},
    )

    values = deal_to_values(deal, source_id=2, fingerprint="def")

    assert values["source_id"] == 2
    assert values["fingerprint"] == "def"
    assert values["price"] == Decimal("299.90")
    assert values["original_price"] == Decimal("399.90")
    assert values["metadata_"] == {"category": "peripherals"}
    assert values["last_seen_at"] == collected_at
