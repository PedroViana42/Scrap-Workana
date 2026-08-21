from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

from radar.config import settings
from radar.discovery.search.base import (
    SearchProvider,
    SearchProviderResponseError,
    SearchProviderUnavailable,
)
from radar.discovery.search.models import SearchResult
from radar.http import HTTPClient, HTTPClientError, HTTPJSONError, HTTPStatusError


class SearXNGSearchProvider(SearchProvider):
    """Low-volume client for Radar's private SearXNG Search API."""

    name = "searxng"
    max_results_per_request = 20

    def __init__(self, base_url: str | None = None, http_client: HTTPClient | None = None) -> None:
        configured_url = settings.searxng_url if base_url is None else base_url
        self.base_url = configured_url.strip().rstrip("/")
        self.endpoint = f"{self.base_url}/search" if self.base_url else ""
        # The service is local, so one conservative retry is enough.
        self._http = http_client or HTTPClient(max_retries=1, backoff_seconds=0.5)
        self.requests_made = 0
        self.results_by_engine: Counter[str] = Counter()
        self.engine_errors: Counter[str] = Counter()

    @property
    def available(self) -> bool:
        return bool(self.base_url)

    def search(
        self,
        query: str,
        *,
        count: int,
        country: str = "BR",
        language: str = "pt",
    ) -> list[SearchResult]:
        if not self.available:
            raise SearchProviderUnavailable("SearXNG Search is unavailable: SEARXNG_URL is empty")
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if not 1 <= count <= self.max_results_per_request:
            raise ValueError(
                f"SearXNG result count must be between 1 and {self.max_results_per_request}"
            )

        self.requests_made += 1
        try:
            payload = self._http.get_json(
                self.endpoint,
                params={
                    "q": query,
                    "format": "json",
                    "language": _searxng_language(language, country),
                    "pageno": 1,
                    "safesearch": 1,
                },
            )
        except HTTPStatusError as exc:
            raise SearchProviderResponseError(
                f"SearXNG Search request failed with HTTP {exc.status_code}"
            ) from exc
        except (HTTPJSONError, HTTPClientError) as exc:
            raise SearchProviderResponseError(
                f"SearXNG Search request failed: {type(exc).__name__}"
            ) from exc

        results, errors = _parse_response(payload, query=query, provider=self.name, count=count)
        for result in results:
            for engine in result.metadata.get("engines", []):
                self.results_by_engine[str(engine)] += 1
        self.engine_errors.update(errors)
        return results


def _parse_response(
    payload: Any,
    *,
    query: str,
    provider: str,
    count: int,
) -> tuple[list[SearchResult], Counter[str]]:
    if not isinstance(payload, Mapping):
        raise SearchProviderResponseError("SearXNG Search response must be an object")
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise SearchProviderResponseError("SearXNG Search response has invalid results")

    parsed: list[SearchResult] = []
    for item in raw_results:
        if not isinstance(item, Mapping):
            raise SearchProviderResponseError("SearXNG Search result must be an object")
        url = _text(item.get("url"))
        if not url:
            continue
        engines = _engines(item)
        parsed.append(
            SearchResult(
                title=_text(item.get("title")) or "Untitled result",
                url=url,
                snippet=_text(item.get("content")),
                query=query,
                provider=provider,
                rank=len(parsed) + 1,
                metadata={
                    key: value
                    for key, value in {
                        "engines": engines,
                        "category": item.get("category"),
                        "score": item.get("score"),
                        "published_date": item.get("publishedDate"),
                    }.items()
                    if value not in (None, [], "")
                },
            )
        )
        if len(parsed) == count:
            break

    errors: Counter[str] = Counter()
    raw_errors = payload.get("unresponsive_engines", [])
    if isinstance(raw_errors, list):
        for error in raw_errors:
            if isinstance(error, (list, tuple)) and error:
                engine = _text(error[0])
                reason = _text(error[1]) if len(error) > 1 else None
                if engine:
                    errors[f"{engine}: {reason or 'unresponsive'}"] += 1
    return parsed, errors


def _engines(item: Mapping[str, Any]) -> list[str]:
    raw = item.get("engines")
    if isinstance(raw, list):
        return [value for entry in raw if (value := _text(entry))]
    engine = _text(item.get("engine"))
    return [engine] if engine else []


def _searxng_language(language: str, country: str) -> str:
    normalized_language = language.strip().replace("_", "-")
    if "-" in normalized_language:
        return normalized_language
    normalized_country = country.strip().upper()
    if normalized_language.casefold() == "pt" and normalized_country == "BR":
        return "pt-BR"
    return normalized_language or "all"


def _text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
