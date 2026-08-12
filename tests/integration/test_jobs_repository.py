from datetime import datetime, timedelta, timezone

import pytest

from radar.database.repositories.jobs import JobRepository
from radar.database.repositories.sources import sync_source_catalog
from radar.models import EmploymentType, Job, RemoteType, Seniority


pytestmark = pytest.mark.integration


def _job(source="greenhouse", external_id="job-1", title="Backend Engineer", collected_at=None):
    return Job(
        source=source,
        external_id=external_id,
        title=title,
        company="Example",
        description="Python and PostgreSQL",
        url=f"https://example.com/{source}/{external_id or title}",
        remote_type=RemoteType.REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        seniority=Seniority.SENIOR,
        technologies=["python", "postgresql"],
        collected_at=collected_at or datetime.now(timezone.utc),
    )


def test_new_job_insert_sets_seen_timestamps(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)

    inserted, created = repository.upsert(_job())
    db_session.commit()

    assert created is True
    assert inserted.first_seen_at is not None
    assert inserted.last_seen_at is not None


def test_same_external_id_updates_without_duplicate_and_preserves_first_seen(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)
    first_time = datetime(2026, 8, 10, 10, tzinfo=timezone.utc)
    second_time = first_time + timedelta(hours=1)

    inserted, created = repository.upsert(_job(collected_at=first_time))
    db_session.commit()
    first_seen = inserted.first_seen_at
    job_id = inserted.id

    updated, created_again = repository.upsert(
        _job(title="Senior Backend Engineer", collected_at=second_time)
    )
    db_session.commit()

    assert created is True
    assert created_again is False
    assert updated.id == job_id
    assert updated.title == "Senior Backend Engineer"
    assert updated.first_seen_at == first_seen
    assert updated.last_seen_at == second_time
    assert db_session.query(updated.__class__).count() == 1


def test_same_fingerprint_without_external_id_upserts(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)
    job = _job(external_id=None, title="Data Engineer")

    inserted, created = repository.upsert(job)
    db_session.commit()
    updated, created_again = repository.upsert(job)
    db_session.commit()

    assert created is True
    assert created_again is False
    assert updated.id == inserted.id
    assert db_session.query(updated.__class__).count() == 1


def test_same_external_id_in_different_sources_is_allowed(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)

    greenhouse_job, _ = repository.upsert(_job(source="greenhouse", external_id="shared-id"))
    lever_job, _ = repository.upsert(_job(source="lever", external_id="shared-id"))
    db_session.commit()

    assert greenhouse_job.id != lever_job.id

