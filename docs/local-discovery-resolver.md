# Local discovery resolver

This experimental component classifies candidate job URLs without collecting or
persisting jobs. A discovery provider is deliberately outside its scope. Search
results can come from a documented search API, an approved partner feed, or a
human-reviewed export; authenticated scraping is not supported.

`DiscoveryCandidate` is not a `Job`. It records where a result was discovered and,
when a reviewer or provider supplies `resolved_url`, the official destination that
was resolved. The resolver never follows redirects or performs network requests.

Input is a JSON array:

```json
[
  {
    "discovered_url": "https://www.linkedin.com/jobs/view/123",
    "resolved_url": "https://company.gupy.io/jobs/456?utm_source=linkedin",
    "observed_title": "Estágio em TI",
    "company": "Example",
    "location": "Goiânia",
    "discovered_via": "linkedin",
    "metadata": {"modality": "hybrid"}
  }
]
```

Run the read-only report with:

```bash
python -m radar.cli discover-local --input results.json
```

The command has no database session and no HTTP client. Its output is intended for
human review before any future, separately authorized ingestion.
