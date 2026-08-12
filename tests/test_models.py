from datetime import datetime, timezone

from radar.models import Deal, EmploymentType, Job, RemoteType, Seniority


def test_job_creation_defaults_unknown_fields():
    job = Job(source="gupy", title="Dev Python Junior", url="https://example.com/job/1")

    assert job.source == "gupy"
    assert job.title == "Dev Python Junior"
    assert job.company is None
    assert job.remote_type is RemoteType.UNKNOWN
    assert job.employment_type is EmploymentType.UNKNOWN
    assert job.seniority is Seniority.UNKNOWN
    assert job.technologies == []
    assert isinstance(job.collected_at, datetime)
    assert job.collected_at.tzinfo == timezone.utc


def test_deal_creation_defaults_unknown_fields():
    deal = Deal(source="store", title="Notebook em promoção", url="https://example.com/deal/1")

    assert deal.source == "store"
    assert deal.image_url is None
    assert deal.price is None
    assert deal.coupon is None
    assert isinstance(deal.collected_at, datetime)


def test_enums_values_are_stable_strings():
    assert RemoteType.REMOTE.value == "remote"
    assert EmploymentType.INTERNSHIP.value == "internship"
    assert EmploymentType.TRAINEE.value == "trainee"
    assert EmploymentType.TEMPORARY.value == "temporary"
    assert Seniority.JUNIOR.value == "junior"
