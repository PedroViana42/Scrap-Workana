from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from radar.api.app import create_app
from radar.api.dependencies import get_session
from radar.database.repositories.jobs import PaginatedJobs


NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def _client(session=None):
    app = create_app()

    def override_session():
        yield session if session is not None else SimpleNamespace()

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def _job(**overrides):
    values = {
        "id": 1,
        "title": "Backend Engineer",
        "company": "Acme",
        "source": SimpleNamespace(name="greenhouse"),
        "description": "Python and SQL",
        "url": "https://example.com/jobs/1",
        "location": "Brazil",
        "remote_type": "remote",
        "employment_type": "full_time",
        "seniority": "junior",
        "salary_min": Decimal("1000.00"),
        "salary_max": Decimal("2000.00"),
        "salary_currency": "USD",
        "technologies": ["Python", "SQL"],
        "published_at": NOW,
        "first_seen_at": NOW,
        "last_seen_at": NOW,
        "relevance_score": 88,
        "relevance_band": "strong",
        "relevance_reasons": {
            "role": ["software"],
            "attainability": {"level": "HIGH", "positive": ["Explicit junior role"], "warnings": [], "negative": []},
        },
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeJobRepository:
    last_filters = None
    last_page = None
    last_page_size = None
    search_result = PaginatedJobs(items=[_job()], total=1)
    detail = _job()

    def __init__(self, session):
        self.session = session

    def search(self, filters, *, page=1, page_size=20):
        FakeJobRepository.last_filters = filters
        FakeJobRepository.last_page = page
        FakeJobRepository.last_page_size = page_size
        return FakeJobRepository.search_result

    def get_by_id(self, job_id):
        return FakeJobRepository.detail if job_id == 1 else None


def test_health_live_does_not_need_database():
    response = _client().get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_checks_database():
    session = SimpleNamespace(execute=lambda statement: SimpleNamespace(scalar_one=lambda: 1))

    response = _client(session).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_reports_database_unavailable():
    def fail(statement):
        raise RuntimeError("down")

    response = _client(SimpleNamespace(execute=fail)).get("/health/ready")

    assert response.status_code == 503


def test_jobs_pagination_and_sort_contract(monkeypatch):
    monkeypatch.setattr("radar.api.routes.jobs.JobRepository", FakeJobRepository)
    FakeJobRepository.search_result = PaginatedJobs(items=[_job(id=1), _job(id=2)], total=42)

    response = _client().get("/jobs?page=2&page_size=10")

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 10
    assert body["total"] == 42
    assert body["pages"] == 5
    assert len(body["items"]) == 2
    assert body["items"][0]["attainability"]["level"] == "HIGH"
    assert FakeJobRepository.last_page == 2
    assert FakeJobRepository.last_page_size == 10


def test_jobs_filters_are_forwarded(monkeypatch):
    monkeypatch.setattr("radar.api.routes.jobs.JobRepository", FakeJobRepository)

    response = _client().get(
        "/jobs?q=python&source=greenhouse&company=Acme&remote=true&employment_type=full_time"
        "&seniority=junior&min_score=70&max_score=90&relevance_band=strong&active=true"
        "&location=Brazil&technology=Python"
        "&attainability=HIGH"
    )

    assert response.status_code == 200
    filters = FakeJobRepository.last_filters
    assert filters.q == "python"
    assert filters.source == "greenhouse"
    assert filters.company == "Acme"
    assert filters.remote is True
    assert filters.employment_type == "full_time"
    assert filters.seniority == "junior"
    assert filters.min_score == 70
    assert filters.max_score == 90
    assert filters.relevance_band == "strong"
    assert filters.active is True
    assert filters.location == "Brazil"
    assert filters.technology == "Python"
    assert filters.attainability == "HIGH"


def test_jobs_reject_invalid_attainability():
    response = _client().get("/jobs?attainability=UNKNOWN")

    assert response.status_code == 422


def test_jobs_invalid_page_size_returns_422():
    response = _client().get("/jobs?page_size=101")

    assert response.status_code == 422


def test_jobs_invalid_score_range_returns_422(monkeypatch):
    monkeypatch.setattr("radar.api.routes.jobs.JobRepository", FakeJobRepository)

    response = _client().get("/jobs?min_score=90&max_score=10")

    assert response.status_code == 422


def test_job_detail_excludes_raw_data(monkeypatch):
    monkeypatch.setattr("radar.api.routes.jobs.JobRepository", FakeJobRepository)
    FakeJobRepository.detail = _job(raw_data={"secret": "payload"})

    response = _client().get("/jobs/1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["salary"]["currency"] == "USD"
    assert "raw_data" not in body
    assert body["attainability"]["positive"] == ["Explicit junior role"]


def test_old_relevance_payload_remains_backwards_compatible(monkeypatch):
    monkeypatch.setattr("radar.api.routes.jobs.JobRepository", FakeJobRepository)
    FakeJobRepository.detail = _job(relevance_reasons={"positive": ["Matched Python"]})

    response = _client().get("/jobs/1")

    assert response.status_code == 200
    assert response.json()["attainability"] is None


def test_job_detail_404(monkeypatch):
    monkeypatch.setattr("radar.api.routes.jobs.JobRepository", FakeJobRepository)

    response = _client().get("/jobs/404")

    assert response.status_code == 404


def test_sources(monkeypatch):
    class FakeSourceRepository:
        def __init__(self, session):
            pass

        def list_all(self):
            return [
                SimpleNamespace(
                    name="greenhouse",
                    display_name="Greenhouse",
                    content_type="job",
                    enabled=True,
                    status="active",
                    collector="greenhouse",
                    priority=10,
                )
            ]

    monkeypatch.setattr("radar.api.routes.sources.SourceRepository", FakeSourceRepository)

    response = _client().get("/sources")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "greenhouse"


def test_stats(monkeypatch):
    class FakeStatsRepository:
        def __init__(self, session):
            pass

        def summary(self):
            return {
                "jobs_total": 10,
                "jobs_active": 8,
                "sources_total": 3,
                "sources_enabled": 3,
                "company_sources_enabled": 45,
                "jobs_by_relevance_band": {"excellent": 1, "strong": 2, "interesting": 3, "low": 1, "very_low": 1},
                "scrape_runs_24h": {"success": 10, "partial": 1, "failed": 0},
                "last_successful_scrape": NOW,
            }

    monkeypatch.setattr("radar.api.routes.stats.StatsRepository", FakeStatsRepository)

    response = _client().get("/stats")

    assert response.status_code == 200
    assert response.json()["jobs_total"] == 10
