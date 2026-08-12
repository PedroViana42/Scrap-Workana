from dataclasses import dataclass
import re

from radar.collectors.base import CollectorResult
from radar.models.job import Job


BRAZIL_TERMS = [
    "brazil",
    "brasil",
    "sao paulo",
    "são paulo",
    "rio de janeiro",
    "belo horizonte",
    "curitiba",
    "florianopolis",
    "florianópolis",
    "brasilia",
    "brasília",
    "porto alegre",
    "recife",
    "campinas",
]

LATAM_TERMS = ["latam", "latin america", "latin-america", "south america", "south-america"]
REMOTE_TERMS = ["remote", "remoto", "remota", "anywhere", "distributed"]
TECH_TERMS = [
    "software",
    "developer",
    "engineer",
    "engineering",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "data",
    "machine learning",
    " ai ",
    " ml ",
    "devops",
    "sre",
    "cloud",
    "platform",
    "infrastructure",
    "security",
    "qa",
    "database",
]
EARLY_CAREER_TERMS = [
    "intern",
    "internship",
    "estagio",
    "estágio",
    "trainee",
    "junior",
    "jr",
    "early career",
    "new grad",
    "graduate",
    "software engineer i",
]


@dataclass(frozen=True)
class CompanyBoardAnalysis:
    total_jobs: int
    jobs_brazil: int
    jobs_latam: int
    jobs_remote: int
    jobs_tech: int
    jobs_early_career: int


def analyze_collector_result(result: CollectorResult) -> CompanyBoardAnalysis:
    jobs = [collected.job for collected in result.jobs]
    return CompanyBoardAnalysis(
        total_jobs=len(jobs),
        jobs_brazil=sum(1 for job in jobs if is_brazil_job(job)),
        jobs_latam=sum(1 for job in jobs if is_latam_job(job)),
        jobs_remote=sum(1 for job in jobs if is_remote_job(job)),
        jobs_tech=sum(1 for job in jobs if is_tech_job(job)),
        jobs_early_career=sum(1 for job in jobs if is_early_career_job(job)),
    )


def is_brazil_job(job: Job) -> bool:
    return _contains_any(_job_text(job, include_description=False), BRAZIL_TERMS)


def is_latam_job(job: Job) -> bool:
    return _contains_any(_job_text(job, include_description=False), LATAM_TERMS)


def is_remote_job(job: Job) -> bool:
    return _contains_any(_job_text(job, include_description=False), REMOTE_TERMS)


def is_tech_job(job: Job) -> bool:
    return _contains_any(_job_text(job), TECH_TERMS)


def is_early_career_job(job: Job) -> bool:
    return _contains_any(_job_text(job), EARLY_CAREER_TERMS)


def _job_text(job: Job, include_description: bool = True) -> str:
    parts = [job.title, job.location or "", " ".join(job.technologies)]
    if include_description:
        parts.append(job.description or "")
    return f" {' '.join(parts).lower()} "


def _contains_any(text: str, terms: list[str]) -> bool:
    normalized = _normalize(text)
    return any(_normalize(term) in normalized for term in terms)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower())

