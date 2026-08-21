from argparse import Namespace

import pytest

from radar.cli import build_parser, discover_local
from radar.discovery.search.base import (
    SearchProviderResponseError,
    SearchProviderUnavailable,
)
from radar.discovery.search.searxng import SearXNGSearchProvider
from radar.discovery.search.service import discover_with_provider
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


def _provider(payload=None, error=None, url="http://searxng:8080"):
    return SearXNGSearchProvider(base_url=url, http_client=FakeHTTPClient(payload, error))


def test_searxng_valid_json_maps_results_parameters_and_engine_metrics():
    provider = _provider({
        "results": [
            {
                "title": "Dev Jr",
                "url": "https://acme.gupy.io/jobs/123",
                "content": "Goiânia",
                "engines": ["duckduckgo", "startpage"],
                "score": 1.5,
            },
            {
                "title": "QA",
                "url": "https://example.com/jobs/qa",
                "engine": "brave",
                "category": "general",
            },
        ],
        "unresponsive_engines": [["startpage", "CAPTCHA"], ["brave", "rate limit"]],
    })

    results = provider.search("Goiânia TI", count=10, country="BR", language="pt")

    assert [result.rank for result in results] == [1, 2]
    assert results[0].provider == "searxng"
    assert results[0].snippet == "Goiânia"
    assert results[0].metadata == {"engines": ["duckduckgo", "startpage"], "score": 1.5}
    assert provider.results_by_engine == {"duckduckgo": 1, "startpage": 1, "brave": 1}
    assert provider.engine_errors == {"startpage: CAPTCHA": 1, "brave: rate limit": 1}
    assert provider._http.calls[0] == {
        "url": "http://searxng:8080/search",
        "params": {
            "q": "Goiânia TI",
            "format": "json",
            "language": "pt-BR",
            "pageno": 1,
            "safesearch": 1,
        },
        "headers": None,
    }


def test_searxng_skips_missing_url_and_caps_first_page_results():
    provider = _provider({
        "results": [
            {"title": "Missing URL"},
            {"title": "First", "url": "https://example.com/1"},
            {"title": "Second", "url": "https://example.com/2"},
        ]
    })
    results = provider.search("query", count=1, country="BR", language="pt-BR")
    assert [result.title for result in results] == ["First"]


def test_searxng_is_unavailable_without_url_and_performs_no_request():
    provider = _provider({"results": []}, url="")
    with pytest.raises(SearchProviderUnavailable, match="SEARXNG_URL is empty"):
        provider.search("query", count=1, country="BR", language="pt")
    assert provider.requests_made == 0
    assert provider._http.calls == []


@pytest.mark.parametrize("error", [
    HTTPStatusError(429, "http://searxng:8080/search"),
    HTTPStatusError(503, "http://searxng:8080/search"),
    HTTPClientError("timeout"),
    HTTPClientError("connection refused"),
    HTTPJSONError("invalid json"),
])
def test_searxng_wraps_rate_limit_server_timeout_unavailable_and_json_errors(error):
    provider = _provider(error=error)
    with pytest.raises(SearchProviderResponseError):
        provider.search("query", count=1, country="BR", language="pt")


def test_searxng_rejects_invalid_payload_result_and_count():
    with pytest.raises(SearchProviderResponseError, match="must be an object"):
        _provider([]).search("query", count=1, country="BR", language="pt")
    with pytest.raises(SearchProviderResponseError, match="invalid results"):
        _provider({}).search("query", count=1, country="BR", language="pt")
    with pytest.raises(SearchProviderResponseError, match="result must be an object"):
        _provider({"results": ["invalid"]}).search("query", count=1, country="BR", language="pt")
    with pytest.raises(ValueError, match="between 1 and 20"):
        _provider({"results": []}).search("query", count=21, country="BR", language="pt")


def test_searxng_integration_resolves_deduplicates_and_saves_replay(tmp_path):
    provider = _provider({
        "results": [
            {"title": "Dev", "url": "https://jobs.lever.co/acme/abcdefgh?utm_source=searxng", "engine": "duckduckgo"},
            {"title": "Dev", "url": "https://jobs.lever.co/acme/abcdefgh?ref=duplicate", "engine": "startpage"},
        ]
    })
    replay = tmp_path / "searxng.json"

    report = discover_with_provider(
        provider, ["Goiânia desenvolvedor"], results_per_query=10, save_results=replay
    )

    assert report.requests_made == 1
    assert len(report.resolution.unique_candidates) == 1
    candidate = report.resolution.unique_candidates[0]
    assert candidate.discovered_via == "searxng"
    assert candidate.probable_source == "lever"
    assert candidate.metadata["engines"] == ["duckduckgo"]
    assert replay.exists()


def test_searxng_cli_provider_engine_metrics_and_existing_replay(monkeypatch, capsys, tmp_path):
    provider = _provider({
        "results": [{"title": "Dev", "url": "https://example.com/jobs/1", "engine": "brave"}],
        "unresponsive_engines": [["startpage", "timeout"]],
    })
    monkeypatch.setattr("radar.discovery.search.searxng.SearXNGSearchProvider", lambda: provider)
    replay = tmp_path / "results.json"
    args = Namespace(
        input=None,
        provider="searxng",
        max_queries=2,
        results_per_query=7,
        save_results=replay,
    )

    assert discover_local(args) == 0
    output = capsys.readouterr().out
    assert "Provider: searxng" in output
    assert "brave: 2" in output
    assert "startpage: timeout: 2" in output
    assert replay.exists()

    parser = build_parser()
    parsed = parser.parse_args(["discover-local", "--provider", "searxng"])
    assert parsed.provider == "searxng"
