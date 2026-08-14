from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from radar.api.app import create_app
from radar.api.dependencies import get_session
from radar.database.models.job import JobDB
from radar.database.repositories.sources import SourceRepository, sync_source_catalog


pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def api_client(db_session):
    app = create_app()

    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def _seed_job(db_session, *, title="Backend Engineer", score=88, active=True, technologies=None):
    sync_source_catalog(db_session)
    source = SourceRepository(db_session).get_by_name("greenhouse")
    job = JobDB(
        source_id=source.id,
        external_id=title.lower().replace(" ", "-"),
        fingerprint=f"fp-{title.lower().replace(' ', '-')}",
        title=title,
        company="Acme",
        description="Python SQL APIs",
        url=f"https://example.com/{title.lower().replace(' ', '-')}",
        location="Brazil",
        remote_type="remote",
        employment_type="full_time",
        seniority="junior",
        technologies=technologies or ["Python", "SQL"],
        published_at=NOW,
        collected_at=NOW,
        first_seen_at=NOW,
        last_seen_at=NOW,
        active=active,
        raw_data={"hidden": True},
        metadata_={},
        relevance_score=score,
        relevance_band="strong",
        relevance_reasons={"role": ["software"]},
    )
    db_session.add(job)
    db_session.commit()
    return job


def test_api_jobs_filters_and_detail_use_database(api_client, db_session):
    job = _seed_job(db_session)
    _seed_job(db_session, title="Inactive Engineer", active=False)

    response = api_client.get("/jobs?q=python&source=greenhouse&remote=true&technology=Python&min_score=70")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == job.id

    detail = api_client.get(f"/jobs/{job.id}")
    assert detail.status_code == 200
    assert detail.json()["description"] == "Python SQL APIs"
    assert "raw_data" not in detail.json()


def test_api_stats_use_database(api_client, db_session):
    _seed_job(db_session)

    response = api_client.get("/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["jobs_total"] == 1
    assert body["jobs_active"] == 1
    assert body["sources_total"] >= 1
