from radar.models.job import Job
from radar.services.company_analysis import (
    is_brazil_job,
    is_early_career_job,
    is_latam_job,
    is_remote_job,
    is_tech_job,
)


def test_detects_brazil_and_latam_locations():
    assert is_brazil_job(Job(source="x", title="Dev", url="u", location="São Paulo, Brazil"))
    assert is_latam_job(Job(source="x", title="Dev", url="u", location="Remote - LATAM"))


def test_detects_remote_tech_and_early_career():
    job = Job(
        source="x",
        title="Junior Software Engineer",
        url="u",
        location="Remote",
        description="Backend platform role",
    )

    assert is_remote_job(job)
    assert is_tech_job(job)
    assert is_early_career_job(job)

