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

Manual-input mode has no database session or HTTP client. Its output is intended
for human review before any future, separately authorized ingestion.

## Brave Search provider

The optional provider uses Brave's documented Web Search endpoint. Configure the
secret only in the runtime environment:

```bash
export BRAVE_SEARCH_API_KEY=...
python -m radar.cli discover-local --provider brave \
  --max-queries 20 --results-per-query 10
```

The defaults are deliberately low-volume. `country=BR`, `search_lang=pt`, and
moderate safe search are sent on every request. The provider delegates timeout,
429/`Retry-After`, conservative retry, and 5xx handling to Radar's HTTP client.

Results can optionally be saved in the manual-input format:

```bash
python -m radar.cli discover-local --provider brave --save-results /tmp/results.json
python -m radar.cli discover-local --input /tmp/results.json
```

Saving is opt-in because Brave plan terms may require explicit storage rights.
The API key and request headers are never included in reports or exceptions.
