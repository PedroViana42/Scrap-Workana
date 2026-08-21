from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from radar.config import settings
from radar.discovery.search.base import (
    SearchProvider,
    SearchProviderAuthenticationError,
    SearchProviderResponseError,
    SearchProviderUnavailable,
)
from radar.discovery.search.models import SearchResult
from radar.http import HTTPClient, HTTPClientError, HTTPJSONError, HTTPStatusError


class TavilySearchProvider(SearchProvider):
    name = "tavily"
    endpoint = "https://api.tavily.com/search"
    max_results_per_request = 20
    estimated_credits_per_request = 1

    def __init__(self, api_key: str | None = None, http_client: HTTPClient | None = None) -> None:
        self._api_key = (api_key if api_key is not None else settings.tavily_api_key) or ""
        # A single retry handles transient 429/5xx without multiplying credit risk.
        self._http = http_client or HTTPClient(max_retries=1, backoff_seconds=1.0)
        self.requests_made = 0

    @property
    def available(self) -> bool:
        return bool(self._api_key.strip())

    def search(
        self,
        query: str,
        *,
        count: int,
        country: str = "BR",
        language: str = "pt",
    ) -> list[SearchResult]:
        if not self.available:
            raise SearchProviderUnavailable(
                "Tavily Search is unavailable: TAVILY_API_KEY is not configured"
            )
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if not 1 <= count <= self.max_results_per_request:
            raise ValueError(f"Tavily result count must be between 1 and {self.max_results_per_request}")

        self.requests_made += 1
        try:
            payload = self._http.post_json(
                self.endpoint,
                payload={
                    "query": query,
                    "search_depth": "basic",
                    "topic": "general",
                    "max_results": count,
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_images": False,
                    "country": _tavily_country(country),
                },
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        except HTTPStatusError as exc:
            if exc.status_code in {401, 403}:
                raise SearchProviderAuthenticationError(
                    f"Tavily Search authentication failed with HTTP {exc.status_code}"
                ) from exc
            raise SearchProviderResponseError(
                f"Tavily Search request failed with HTTP {exc.status_code}"
            ) from exc
        except (HTTPJSONError, HTTPClientError) as exc:
            raise SearchProviderResponseError(
                f"Tavily Search request failed: {type(exc).__name__}"
            ) from exc

        # Tavily has no documented search-language parameter. The interface value
        # is intentionally not sent; the explicit Portuguese query controls language.
        del language
        return _parse_results(payload, query=query, provider=self.name)


def _parse_results(payload: Any, *, query: str, provider: str) -> list[SearchResult]:
    if not isinstance(payload, Mapping):
        raise SearchProviderResponseError("Tavily Search response must be an object")
    results = payload.get("results")
    if not isinstance(results, list):
        raise SearchProviderResponseError("Tavily Search response has invalid results")

    parsed: list[SearchResult] = []
    for rank, item in enumerate(results, 1):
        if not isinstance(item, Mapping):
            raise SearchProviderResponseError("Tavily Search result must be an object")
        url = _text(item.get("url"))
        if not url:
            continue
        parsed.append(
            SearchResult(
                title=_text(item.get("title")) or "Untitled result",
                url=url,
                snippet=_text(item.get("content")),
                query=query,
                provider=provider,
                rank=rank,
                metadata={
                    key: value
                    for key, value in {
                        "score": item.get("score"),
                        "published_date": item.get("published_date"),
                    }.items()
                    if value is not None
                },
            )
        )
    return parsed


def _tavily_country(country: str) -> str:
    normalized = country.strip().casefold()
    return "brazil" if normalized in {"br", "brazil", "brasil"} else normalized


def _text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
