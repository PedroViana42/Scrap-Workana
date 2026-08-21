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

## Search providers

### SearXNG (recommended for self-hosted discovery)

Radar's recommended provider is a private SearXNG instance on the Compose network.
It uses the official `/search` API with JSON output, the shared 18-query set,
Portuguese/Brazil locale, moderate safe search, and only the first result page.

```bash
export SEARXNG_URL=http://searxng:8080
python -m radar.cli discover-local --provider searxng \
  --max-queries 18 --results-per-query 10
```

The production Compose definition publishes no SearXNG port. Only containers on
the private Compose network can use it. Its allowlist contains DuckDuckGo, Brave
Web, and Startpage; none requires an API key. Upstream failures and the engines
that contributed each result are reported without attempting CAPTCHA bypasses.

The local configuration explicitly enables `html` and `json`, because SearXNG
returns HTTP 403 for output formats not enabled in `settings.yml`. `time_range`
is supported by the API but intentionally omitted for the initial benchmark.

### Tavily (optional commercial provider)

Tavily Basic Search remains an optional low-volume provider. Its Researcher plan
currently advertises 1,000 free credits per month without a credit card, and a
Basic Search currently costs one credit. Verify current plan and pricing terms
before production automation.

```bash
export TAVILY_API_KEY=...
python -m radar.cli discover-local --provider tavily \
  --max-queries 18 --results-per-query 10
```

The provider calls only Tavily Search with `search_depth=basic`, `topic=general`,
no generated answer, no raw content, no images, and `country=brazil`. Tavily has
no equivalent documented search-language parameter, so location and Portuguese
intent remain explicit in the shared query set. At 18 queries once per day, the
estimated use is 18 credits/day or approximately 540 credits in a 30-day month.

### Brave (optional)

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

Saving is opt-in because provider plan terms may constrain storage rights. API
keys and request headers are never included in reports or exceptions.
