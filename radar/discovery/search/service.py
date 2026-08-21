from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from radar.discovery.resolver import LocalDiscoveryResolver, ResolutionReport, normalize_url
from radar.discovery.search.base import SearchProvider
from radar.discovery.search.models import SearchResult


@dataclass(frozen=True)
class SearchDiscoveryReport:
    queries_executed: int
    requests_made: int
    raw_results: int
    filtered_results: int
    resolution: ResolutionReport
    estimated_cost_usd: float | None
    estimated_credits: int | None


def discover_with_provider(
    provider: SearchProvider,
    queries: list[str],
    *,
    results_per_query: int,
    country: str = "BR",
    language: str = "pt",
    save_results: Path | None = None,
) -> SearchDiscoveryReport:
    results: list[SearchResult] = []
    for query in queries:
        results.extend(
            provider.search(query, count=results_per_query, country=country, language=language)
        )

    rows = [search_result_to_resolver_input(result) for result in results if is_useful_result(result)]
    if save_results is not None:
        save_results.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    resolution = LocalDiscoveryResolver().resolve_all(rows)
    unit_cost = provider.estimated_cost_per_request_usd
    estimated_cost = provider.requests_made * unit_cost if unit_cost is not None else None
    unit_credits = provider.estimated_credits_per_request
    estimated_credits = provider.requests_made * unit_credits if unit_credits is not None else None
    return SearchDiscoveryReport(
        queries_executed=len(queries),
        requests_made=provider.requests_made,
        raw_results=len(results),
        filtered_results=len(rows),
        resolution=resolution,
        estimated_cost_usd=estimated_cost,
        estimated_credits=estimated_credits,
    )


def search_result_to_resolver_input(result: SearchResult) -> dict[str, object]:
    metadata: dict[str, object] = {
        "snippet": result.snippet,
        "query": result.query,
        "provider": result.provider,
        "rank": result.rank,
        **result.metadata,
    }
    return {
        "discovered_url": result.url,
        "observed_title": result.title,
        "discovered_via": result.provider,
        "metadata": {key: value for key, value in metadata.items() if value is not None},
    }


def is_useful_result(result: SearchResult) -> bool:
    try:
        normalized = normalize_url(result.url)
    except (ValueError, UnicodeError):
        return False
    parsed = urlsplit(normalized)
    path = parsed.path.casefold().rstrip("/")
    host = (parsed.hostname or "").casefold()
    if path.endswith(".pdf"):
        return False
    if host.endswith("linkedin.com") and path in {"/jobs", "/jobs/search"}:
        return False
    if host.endswith("gupy.io") and path in {"", "/"}:
        return False
    if host in {"google.com", "www.google.com", "search.brave.com"}:
        return False
    return True
