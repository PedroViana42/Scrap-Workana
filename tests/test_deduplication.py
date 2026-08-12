from radar.models.job import Job
from radar.services.deduplication import generate_fingerprint, job_fingerprint, normalize_token


def test_normalize_token_removes_accents_and_extra_spaces():
    assert normalize_token("  Desenvolvedor  São Paulo  ") == "desenvolvedor sao paulo"


def test_fingerprint_prioritizes_external_id():
    first = generate_fingerprint(
        source="Gupy",
        external_id="ABC-123",
        url="https://example.com/old",
        title="Old title",
        company="A",
    )
    second = generate_fingerprint(
        source="gupy",
        external_id="abc-123",
        url="https://example.com/new",
        title="New title",
        company="B",
    )

    assert first == second


def test_job_fingerprint_is_stable_without_external_id():
    job = Job(
        source="LinkedIn",
        title="Engenheiro de Dados",
        company="Acme",
        url="https://example.com/jobs/1",
    )

    assert job_fingerprint(job) == generate_fingerprint(
        source="linkedin",
        title="engenheiro de dados",
        company="acme",
        url="https://example.com/jobs/1",
    )

