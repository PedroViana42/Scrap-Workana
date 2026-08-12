from radar.models.enums import RemoteType, Seniority
from radar.models.job import Job
from radar.services.job_filter import (
    JobInterestCriteria,
    classify_job,
    find_technical_keywords,
    infer_remote_type,
    infer_seniority,
    is_interesting_job,
    normalize_text,
)


def test_normalize_text_removes_accents_and_lowercases():
    assert normalize_text("Automação com IA em São Paulo") == "automacao com ia em sao paulo"


def test_technical_filter_accepts_python_remote_job():
    job = Job(
        source="test",
        title="Desenvolvedor Python Junior Remoto",
        url="https://example.com",
        description="API com FastAPI e PostgreSQL",
    )

    accepted, keywords = classify_job(job)

    assert accepted is True
    assert "python" in keywords
    assert "fastapi" in keywords
    assert is_interesting_job(job) is True


def test_filter_rejects_when_no_technology_matches():
    job = Job(
        source="test",
        title="Analista administrativo",
        url="https://example.com",
        description="Rotinas operacionais",
    )

    assert classify_job(job) == (False, [])


def test_find_technical_keywords_supports_future_stack_terms():
    matches = find_technical_keywords("ETL com Snowflake, Airflow e Machine Learning")

    assert "etl" in matches
    assert "snowflake" in matches
    assert "airflow" in matches
    assert "machine learning" in matches


def test_filter_can_limit_by_remote_type_and_seniority():
    criteria = JobInterestCriteria(
        seniorities={Seniority.JUNIOR},
        remote_types={RemoteType.REMOTE},
    )
    job = Job(
        source="test",
        title="Desenvolvedor Python Junior",
        url="https://example.com",
        description="Vaga remota com SQL",
        seniority=Seniority.JUNIOR,
        remote_type=RemoteType.REMOTE,
    )

    assert classify_job(job, criteria)[0] is True


def test_infer_seniority_and_remote_type_from_text():
    assert infer_seniority("Programa de estágio em dados") is Seniority.INTERN
    assert infer_seniority("Pessoa desenvolvedora senior") is Seniority.SENIOR
    assert infer_remote_type("Vaga híbrida em São Paulo") is RemoteType.HYBRID
    assert infer_remote_type("Posição presencial") is RemoteType.ONSITE
