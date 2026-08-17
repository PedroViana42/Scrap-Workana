from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from radar.database.models.job import JobDB
from radar.database.repositories.jobs import JobRepository
from radar.database.repositories.sources import sync_source_catalog
from radar.models import Job
from radar.relevance.scoring import score_job


pytestmark = pytest.mark.integration


def test_job_relevance_is_persisted_with_json_and_version(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)
    job = Job(
        source="greenhouse",
        external_id="rel-1",
        title="Junior Backend Engineer",
        company="Example",
        description="Python PostgreSQL",
        url="https://example.com/rel-1",
        location="Remote Brazil",
        collected_at=datetime.now(timezone.utc),
    )

    job_db, _ = repository.upsert(job)
    result = score_job(job)
    repository.update_relevance(job_db.id, result, technologies=job.technologies)
    db_session.commit()

    stored = db_session.get(JobDB, job_db.id)
    assert stored.relevance_score == result.score
    assert stored.relevance_band == result.band.value
    assert stored.relevance_reasons["positive"]
    assert stored.relevance_components["role"] >= 0
    assert stored.relevance_version == result.version
    assert stored.scored_at is not None
    assert "Python" in stored.technologies


def test_relevance_score_constraint_rejects_invalid_values(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    source_id = db_session.execute(text("select id from sources where name='greenhouse'")).scalar_one()

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                """
                insert into jobs (
                    source_id, fingerprint, title, url, remote_type, employment_type, seniority,
                    technologies, collected_at, active, metadata, raw_data, relevance_score
                )
                values (
                    :source_id, 'bad-score', 'Bad', 'https://example.com/bad',
                    'unknown', 'unknown', 'unknown', ARRAY[]::varchar[],
                    now(), true, '{}'::jsonb, '{}'::jsonb, 101
                )
                """
            ),
            {"source_id": source_id},
        )
        db_session.flush()


def test_list_active_by_relevance_orders_desc(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)
    low, _ = repository.upsert(Job(source="greenhouse", external_id="low", title="Marketing Manager", url="https://example.com/low", location="Brazil"))
    high, _ = repository.upsert(Job(source="greenhouse", external_id="high", title="Junior Backend Engineer", url="https://example.com/high", location="Remote Brazil", description="Python"))
    repository.update_relevance(low.id, score_job(Job(source="greenhouse", external_id="low", title="Marketing Manager", url="https://example.com/low", location="Brazil")))
    job = Job(source="greenhouse", external_id="high", title="Junior Backend Engineer", url="https://example.com/high", location="Remote Brazil", description="Python")
    repository.update_relevance(high.id, score_job(job), technologies=job.technologies)
    db_session.commit()

    ordered = repository.list_active_by_relevance(limit=2)
    assert ordered[0].id == high.id


def test_list_for_rescore_uses_keyset_batches_and_can_skip_current_version(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = JobRepository(db_session)
    jobs = []
    for index in range(5):
        job, _ = repository.upsert(
            Job(
                source="greenhouse",
                external_id=f"batch-{index}",
                title=f"Software Engineer {index}",
                url=f"https://example.com/batch-{index}",
            )
        )
        jobs.append(job)
    jobs[1].active = False
    jobs[2].relevance_version = "tech_early_career_br:v1.2"
    db_session.commit()

    first = repository.list_for_rescore(limit=2)
    second = repository.list_for_rescore(after_id=first[-1].id, limit=2)
    outdated = repository.list_for_rescore(
        limit=10,
        exclude_version="tech_early_career_br:v1.2",
    )
    active = repository.list_for_rescore(limit=10, active_only=True)

    assert [job.id for job in first] == [jobs[0].id, jobs[1].id]
    assert [job.id for job in second] == [jobs[2].id, jobs[3].id]
    assert jobs[1].id in {job.id for job in outdated}
    assert jobs[2].id not in {job.id for job in outdated}
    assert jobs[1].id not in {job.id for job in active}
