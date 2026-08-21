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


class BraveSearchProvider(SearchProvider):
    name = "brave"
    endpoint = "https://api.search.brave.com/res/v1/web/search"
    max_results_per_request = 20
    estimated_cost_per_request_usd = 0.005

    def __init__(self, api_key: str | None = None, http_client: HTTPClient | None = None) -> None:
        self._api_key = (api_key if api_key is not None else settings.brave_search_api_key) or ""
        self._http = http_client or HTTPClient(max_retries=2, backoff_seconds=1.0)
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
                "Brave Search is unavailable: BRAVE_SEARCH_API_KEY is not configured"
            )
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if not 1 <= count <= self.max_results_per_request:
            raise ValueError(f"Brave result count must be between 1 and {self.max_results_per_request}")

        self.requests_made += 1
        try:
            payload = self._http.get_json(
                self.endpoint,
                params={
                    "q": query,
                    "count": count,
                    "country": country.upper(),
                    "search_lang": language.casefold(),
                    "safesearch": "moderate",
                },
                headers={"X-Subscription-Token": self._api_key},
            )
        except HTTPStatusError as exc:
            if exc.status_code in {401, 403}:
                raise SearchProviderAuthenticationError(
                    f"Brave Search authentication failed with HTTP {exc.status_code}"
                ) from exc
            raise SearchProviderResponseError(
                f"Brave Search request failed with HTTP {exc.status_code}"
            ) from exc
        except (HTTPJSONError, HTTPClientError) as exc:
            raise SearchProviderResponseError(
                f"Brave Search request failed: {type(exc).__name__}"
            ) from exc

        return _parse_results(payload, query=query, provider=self.name)


def _parse_results(payload: Any, *, query: str, provider: str) -> list[SearchResult]:
    if not isinstance(payload, Mapping):
        raise SearchProviderResponseError("Brave Search response must be an object")
    web = payload.get("web")
    if web is None:
        return []
    if not isinstance(web, Mapping) or not isinstance(web.get("results"), list):
        raise SearchProviderResponseError("Brave Search response has invalid web results")

    parsed: list[SearchResult] = []
    for rank, item in enumerate(web["results"], 1):
        if not isinstance(item, Mapping):
            raise SearchProviderResponseError("Brave Search result must be an object")
        url = _text(item.get("url"))
        if not url:
            continue
        parsed.append(
            SearchResult(
                title=_text(item.get("title")) or "Untitled result",
                url=url,
                snippet=_text(item.get("description")),
                query=query,
                provider=provider,
                rank=rank,
                metadata={
                    key: value
                    for key, value in {
                        "age": item.get("age"),
                        "language": item.get("language"),
                    }.items()
                    if value is not None
                },
            )
        )
    return parsed


def _text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
