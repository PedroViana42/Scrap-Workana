from argparse import Namespace
from pathlib import Path

import pytest

from radar.cli import build_parser, discover_local
from radar.discovery.queries import LocalDiscoveryQuerySet
from radar.discovery.reporting import resolve_file
from radar.discovery.search.base import (
    SearchProvider,
    SearchProviderAuthenticationError,
    SearchProviderResponseError,
    SearchProviderUnavailable,
)
from radar.discovery.search.brave import BraveSearchProvider
from radar.discovery.search.models import SearchResult
from radar.discovery.search.service import discover_with_provider, is_useful_result
from radar.http import HTTPClientError, HTTPJSONError, HTTPStatusError


class FakeHTTPClient:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        if self.error:
            raise self.error
        return self.payload


class FakeProvider(SearchProvider):
    name = "fake"
    estimated_cost_per_request_usd = 0.01

    def __init__(self, result_factory=None):
        self.requests_made = 0
        self.calls = []
        self.result_factory = result_factory

    def search(self, query, *, count, country, language):
        self.requests_made += 1
        self.calls.append((query, count, country, language))
        if self.result_factory:
            return self.result_factory(query)
        return []


def _result(url, *, query="query", rank=1, title="Developer"):
    return SearchResult(title, url, "snippet", query, "brave", rank)


def test_brave_parses_valid_multiple_results_and_request_parameters():
    http = FakeHTTPClient({
        "web": {
            "results": [
                {"title": "Dev Jr", "url": "https://acme.gupy.io/jobs/123", "description": "Goiânia", "age": "1 day"},
                {"title": "QA", "url": "https://acme.example/jobs/qa", "language": "pt"},
            ]
        }
    })
    provider = BraveSearchProvider(api_key="secret-value", http_client=http)

    results = provider.search("Goiânia TI", count=10, country="br", language="PT")

    assert [result.rank for result in results] == [1, 2]
    assert results[0].snippet == "Goiânia"
    assert results[0].metadata == {"age": "1 day"}
    assert provider.requests_made == 1
    assert http.calls[0]["params"] == {
        "q": "Goiânia TI", "count": 10, "country": "BR", "search_lang": "pt", "safesearch": "moderate"
    }
    assert http.calls[0]["headers"] == {"X-Subscription-Token": "secret-value"}


def test_brave_skips_result_without_url_and_allows_empty_web_section():
    provider = BraveSearchProvider(
        api_key="key",
        http_client=FakeHTTPClient({"web": {"results": [{"title": "Missing URL"}]}}),
    )
    assert provider.search("query", count=1, country="BR", language="pt") == []
    empty = BraveSearchProvider(api_key="key", http_client=FakeHTTPClient({}))
    assert empty.search("query", count=1, country="BR", language="pt") == []


def test_brave_is_unavailable_without_api_key():
    provider = BraveSearchProvider(api_key="", http_client=FakeHTTPClient({}))
    with pytest.raises(SearchProviderUnavailable, match="not configured"):
        provider.search("query", count=1, country="BR", language="pt")
    assert provider.requests_made == 0


@pytest.mark.parametrize("status", [401, 403])
def test_brave_maps_authentication_errors_without_key(status):
    provider = BraveSearchProvider(
        api_key="do-not-leak",
        http_client=FakeHTTPClient(error=HTTPStatusError(status, BraveSearchProvider.endpoint)),
    )
    with pytest.raises(SearchProviderAuthenticationError) as exc:
        provider.search("query", count=1, country="BR", language="pt")
    assert "do-not-leak" not in str(exc.value)


@pytest.mark.parametrize("error", [
    HTTPStatusError(429, BraveSearchProvider.endpoint),
    HTTPStatusError(503, BraveSearchProvider.endpoint),
    HTTPClientError("timeout"),
    HTTPJSONError("invalid json"),
])
def test_brave_wraps_rate_limit_server_timeout_and_json_errors(error):
    provider = BraveSearchProvider(api_key="key", http_client=FakeHTTPClient(error=error))
    with pytest.raises(SearchProviderResponseError):
        provider.search("query", count=1, country="BR", language="pt")


def test_brave_rejects_invalid_payload_and_count():
    provider = BraveSearchProvider(api_key="key", http_client=FakeHTTPClient([]))
    with pytest.raises(SearchProviderResponseError, match="must be an object"):
        provider.search("query", count=1, country="BR", language="pt")
    with pytest.raises(ValueError, match="between 1 and 20"):
        provider.search("query", count=21, country="BR", language="pt")


def test_search_integration_converts_resolves_deduplicates_and_saves_replay(tmp_path):
    def results(query):
        return [
            _result("https://acme.gupy.io/jobs/123?utm_source=brave", query=query),
            _result("https://acme.gupy.io/jobs/123?ref=duplicate", query=query, rank=2),
        ]

    provider = FakeProvider(results)
    replay = tmp_path / "results.json"
    report = discover_with_provider(
        provider, ["query one", "query two"], results_per_query=5, save_results=replay
    )

    assert report.queries_executed == 2
    assert report.requests_made == 2
    assert report.raw_results == 4
    assert len(report.resolution.unique_candidates) == 1
    candidate = report.resolution.unique_candidates[0]
    assert candidate.discovered_via == "brave"
    assert candidate.probable_source == "gupy"
    assert candidate.metadata["query"] == "query one"
    assert report.estimated_cost_usd == 0.02
    assert replay.read_text().startswith("[\n")
    assert len(resolve_file(replay).unique_candidates) == 1


@pytest.mark.parametrize("url", [
    "not-a-url",
    "https://example.com/file.pdf",
    "https://linkedin.com/jobs/search?keywords=TI",
    "https://acme.gupy.io/",
    "https://search.brave.com/search?q=jobs",
])
def test_initial_filter_discards_obviously_useless_results(url):
    assert not is_useful_result(_result(url))


def test_initial_filter_keeps_uncertain_and_supported_postings():
    assert is_useful_result(_result("https://company.example/carreiras/oportunidade"))
    assert is_useful_result(_result("https://jobs.lever.co/acme/12345678"))


def test_query_set_is_small_deliberate_and_covers_all_local_areas():
    queries = list(LocalDiscoveryQuerySet().iter_queries())
    assert len(queries) <= 20
    for city in ("Goiânia", "Aparecida de Goiânia", "Senador Canedo", "Trindade", "Goianira"):
        assert any(city in query for query in queries)
    assert any("site:gupy.io" in query for query in queries)
    assert any("site:linkedin.com/jobs" in query for query in queries)


def test_cli_parser_preserves_input_and_accepts_provider_limits(tmp_path):
    parser = build_parser()
    manual = parser.parse_args(["discover-local", "--input", str(tmp_path / "input.json")])
    assert manual.input == tmp_path / "input.json"
    automated = parser.parse_args([
        "discover-local", "--provider", "brave", "--max-queries", "5", "--results-per-query", "10"
    ])
    assert automated.provider == "brave"
    assert automated.max_queries == 5
    assert automated.results_per_query == 10
    tavily = parser.parse_args(["discover-local", "--provider", "tavily"])
    assert tavily.provider == "tavily"
    with pytest.raises(SystemExit):
        parser.parse_args(["discover-local", "--provider", "brave", "--max-queries", "21"])
    with pytest.raises(SystemExit):
        parser.parse_args(["discover-local", "--provider", "brave", "--results-per-query", "21"])


def test_existing_input_cli_still_works(capsys):
    args = Namespace(input=Path("tests/fixtures/local_discovery_results.json"))
    assert discover_local(args) == 0
    assert "Candidates found: 12" in capsys.readouterr().out


def test_provider_cli_respects_max_queries_and_results_per_query(monkeypatch, capsys):
    fake = FakeProvider()
    monkeypatch.setattr("radar.discovery.search.brave.BraveSearchProvider", lambda: fake)
    args = Namespace(
        input=None, provider="brave", max_queries=3, results_per_query=7, save_results=None
    )
    assert discover_local(args) == 0
    assert len(fake.calls) == 3
    assert all(call[1:] == (7, "BR", "pt") for call in fake.calls)
    assert "Queries executed: 3" in capsys.readouterr().out
