from dataclasses import dataclass, field
import re
import unicodedata

from radar.models.enums import RemoteType, Seniority
from radar.models.job import Job


TECH_KEYWORDS = [
    "python",
    "java",
    "c#",
    ".net",
    "node.js",
    "node",
    "typescript",
    "javascript",
    "react",
    "next.js",
    "nextjs",
    "fastapi",
    "nestjs",
    "django",
    "sql",
    "postgresql",
    "mysql",
    "snowflake",
    "airflow",
    "etl",
    "data engineering",
    "machine learning",
    "ia",
    "ai",
    "automacao",
    "backend",
    "fullstack",
    "dados",
    "api",
    "bot",
    "scraping",
    "mvp",
    "saas",
    "agente",
    "landing page",
    "desenvolvimento",
]

SENIORITY_KEYWORDS = {
    Seniority.INTERN: ["estagio", "estagiario", "internship"],
    Seniority.JUNIOR: ["junior", "jr"],
    Seniority.MID: ["pleno", "mid-level", "mid level"],
    Seniority.SENIOR: ["senior", "sr"],
    Seniority.LEAD: ["lead", "lider", "tech lead"],
}

REMOTE_TYPE_KEYWORDS = {
    RemoteType.REMOTE: ["remoto", "remote"],
    RemoteType.HYBRID: ["hibrido", "hibrida", "hybrid"],
    RemoteType.ONSITE: ["presencial", "onsite"],
}


@dataclass
class JobInterestCriteria:
    technologies: list[str] = field(default_factory=lambda: TECH_KEYWORDS.copy())
    seniorities: set[Seniority] = field(default_factory=set)
    remote_types: set[RemoteType] = field(default_factory=set)
    locations: list[str] = field(default_factory=list)
    include_internship: bool = True
    include_junior: bool = True


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value.lower()).strip()


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)
    return re.search(rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)", text) is not None


def find_technical_keywords(text: str, technologies: list[str] | None = None) -> list[str]:
    normalized = normalize_text(text)
    configured_technologies = technologies or TECH_KEYWORDS
    matches = [
        tech
        for tech in configured_technologies
        if _contains_keyword(normalized, tech)
    ]
    return sorted(set(matches), key=str.lower)


def infer_seniority(text: str) -> Seniority:
    normalized = normalize_text(text)
    for seniority, keywords in SENIORITY_KEYWORDS.items():
        if any(_contains_keyword(normalized, keyword) for keyword in keywords):
            return seniority
    return Seniority.UNKNOWN


def infer_remote_type(text: str) -> RemoteType:
    normalized = normalize_text(text)
    for remote_type, keywords in REMOTE_TYPE_KEYWORDS.items():
        if any(_contains_keyword(normalized, keyword) for keyword in keywords):
            return remote_type
    return RemoteType.UNKNOWN


def classify_job(job: Job, criteria: JobInterestCriteria | None = None) -> tuple[bool, list[str]]:
    criteria = criteria or JobInterestCriteria()
    text = " ".join([job.title, job.company or "", job.description or "", job.location or ""])
    normalized = normalize_text(text)

    if criteria.seniorities and job.seniority not in criteria.seniorities:
        return False, []

    if criteria.remote_types and job.remote_type not in criteria.remote_types:
        return False, []

    if criteria.locations:
        normalized_locations = [normalize_text(location) for location in criteria.locations]
        if not any(location in normalized for location in normalized_locations):
            return False, []

    technical_keywords = find_technical_keywords(normalized, criteria.technologies)
    return bool(technical_keywords), technical_keywords


def is_interesting_job(job: Job, criteria: JobInterestCriteria | None = None) -> bool:
    accepted, _ = classify_job(job, criteria)
    return accepted
