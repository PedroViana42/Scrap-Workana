import re
import unicodedata


TECH_ALIASES: dict[str, list[str]] = {
    "Python": [r"python"],
    "SQL": [r"sql"],
    "PostgreSQL": [r"postgresql", r"postgres"],
    "FastAPI": [r"fastapi", r"fast api"],
    "Airflow": [r"airflow", r"apache airflow"],
    "Snowflake": [r"snowflake"],
    "Machine Learning": [r"machine learning", r"\bml\b"],
    "LLM": [r"large language model", r"large language models", r"\bllm\b", r"\bllms\b"],
    "AI": [r"artificial intelligence", r"\bai\b", r"\bia\b"],
    "Data Engineering": [r"data engineering", r"data engineer"],
    "C#": [r"c#", r"c sharp"],
    ".NET": [r"\.net", r"dotnet", r"asp\.net"],
    "Node.js": [r"node\.js", r"nodejs", r"\bnode\b"],
    "TypeScript": [r"typescript", r"\bts\b"],
    "JavaScript": [r"javascript", r"\bjs\b"],
    "NestJS": [r"nestjs", r"nest\.js"],
    "React": [r"react", r"react\.js"],
    "Next.js": [r"next\.js", r"nextjs"],
    "Docker": [r"docker"],
    "Git": [r"\bgit\b"],
    "REST API": [r"rest api", r"restful api", r"\bapis?\b"],
    "Kubernetes": [r"kubernetes", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"amazon web services"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"google cloud"],
    "Redis": [r"redis"],
    "Kafka": [r"kafka"],
    "dbt": [r"\bdbt\b"],
    "Spark": [r"apache spark", r"\bspark\b"],
}


def detect_technologies(title: str | None, description: str | None) -> list[str]:
    text = f"{title or ''} {description or ''}"
    normalized = _normalize(text)
    matches: list[str] = []
    for canonical, aliases in TECH_ALIASES.items():
        if any(re.search(_bounded(pattern), normalized) for pattern in aliases):
            matches.append(canonical)
    return sorted(set(matches))


def _bounded(pattern: str) -> str:
    if pattern.startswith("\\b") or pattern.startswith("."):
        return pattern
    return rf"(?<![a-z0-9+#.]){pattern}(?![a-z0-9+#.])"


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value)

