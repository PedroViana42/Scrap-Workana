import hashlib
import re
import unicodedata

from radar.models.job import Job


def normalize_token(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value.lower()).strip()


def generate_fingerprint(
    *,
    source: str,
    external_id: str | None = None,
    url: str | None = None,
    title: str | None = None,
    company: str | None = None,
) -> str:
    normalized_source = normalize_token(source)
    normalized_external_id = normalize_token(external_id)

    if normalized_external_id:
        raw = f"{normalized_source}:external:{normalized_external_id}"
    else:
        raw = ":".join(
            [
                normalized_source,
                normalize_token(url),
                normalize_token(title),
                normalize_token(company),
            ]
        )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def job_fingerprint(job: Job) -> str:
    return generate_fingerprint(
        source=job.source,
        external_id=job.external_id,
        url=job.url,
        title=job.title,
        company=job.company,
    )

