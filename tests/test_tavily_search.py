from argparse import Namespace

import pytest

from radar.cli import discover_local
from radar.discovery.search.base import (
    SearchProviderAuthenticationError,
    SearchProviderResponseError,
    SearchProviderUnavailable,
)
from radar.discovery.search.service import discover_with_provider
from radar.discovery.search.tavily import TavilySearchProvider
from radar.http import HTTPClientError, HTTPJSONError, HTTPStatusError


class FakeHTTPClient:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def post_json(self, url, payload, headers=None):
        self.calls.append({"url": url, "payload": payload, "headers": headers})
        if self.error:
            raise self.error
        return self.payload


def _provider(payload=None, error=None, key="test-key"):
    return TavilySearchProvider(api_key=key, http_client=FakeHTTPClient(payload, error))


def test_tavily_valid_response_multiple_results_and_basic_parameters():
    provider = _provider({
        "query": "Goiânia TI",
        "results": [
            {"title": "Dev Jr", "url": "https://acme.gupy.io/jobs/123", "content": "Vaga local", "score": 0.9},
            {"title": "QA", "url": "https://acme.example/jobs/qa", "content": "Testes", "published_date": "2026-08-20"},
        ],
        "usage": {"credits": 1},
    })

    results = provider.search("Goiânia TI", count=10, country="BR", language="pt")

    assert [item.rank for item in results] == [1, 2]
    assert results[0].provider == "tavily"
    assert results[0].snippet == "Vaga local"
    assert results[0].metadata == {"score": 0.9}
    call = provider._http.calls[0]
    assert call["payload"] == {
        "query": "Goiânia TI",
        "search_depth": "basic",
        "topic": "general",
        "max_results": 10,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
        "country": "brazil",
    }
    assert "language" not in call["payload"]
    assert call["headers"] == {"Authorization": "Bearer test-key"}


def test_tavily_skips_result_without_url():
    provider = _provider({"results": [{"title": "Missing URL"}]})
    assert provider.search("query", count=1, country="BR", language="pt") == []


def test_tavily_missing_key_performs_no_request():
    provider = _provider({"results": []}, key="")
    with pytest.raises(SearchProviderUnavailable, match="not configured"):
        provider.search("query", count=1, country="BR", language="pt")
    assert provider.requests_made == 0
    assert provider._http.calls == []


@pytest.mark.parametrize("status", [401, 403])
def test_tavily_authentication_error_does_not_expose_key(status):
    provider = _provider(error=HTTPStatusError(status, TavilySearchProvider.endpoint), key="hidden-key")
    with pytest.raises(SearchProviderAuthenticationError) as exc:
        provider.search("query", count=1, country="BR", language="pt")
    assert "hidden-key" not in str(exc.value)


@pytest.mark.parametrize("error", [
    HTTPStatusError(429, TavilySearchProvider.endpoint),
    HTTPStatusError(500, TavilySearchProvider.endpoint),
    HTTPClientError("timeout"),
    HTTPJSONError("invalid json"),
])
def test_tavily_wraps_rate_limit_server_timeout_and_json_errors(error):
    provider = _provider(error=error)
    with pytest.raises(SearchProviderResponseError):
        provider.search("query", count=1, country="BR", language="pt")


def test_tavily_invalid_payload_and_max_results():
    with pytest.raises(SearchProviderResponseError, match="must be an object"):
        _provider([]).search("query", count=1, country="BR", language="pt")
    with pytest.raises(SearchProviderResponseError, match="invalid results"):
        _provider({}).search("query", count=1, country="BR", language="pt")
    with pytest.raises(ValueError, match="between 1 and 20"):
        _provider({"results": []}).search("query", count=21, country="BR", language="pt")


def test_tavily_integration_resolves_deduplicates_saves_and_estimates_credits(tmp_path):
    provider = _provider({
        "results": [
            {"title": "Dev", "url": "https://jobs.lever.co/acme/abcdefgh?utm_source=tavily", "content": "Junior"},
            {"title": "Dev", "url": "https://jobs.lever.co/acme/abcdefgh?ref=duplicate", "content": "Junior"},
        ]
    })
    replay = tmp_path / "tavily.json"

    report = discover_with_provider(
        provider, ["Goiânia desenvolvedor"], results_per_query=10, save_results=replay
    )

    assert report.requests_made == 1
    assert report.estimated_credits == 1
    assert report.estimated_cost_usd is None
    assert len(report.resolution.unique_candidates) == 1
    candidate = report.resolution.unique_candidates[0]
    assert candidate.discovered_via == "tavily"
    assert candidate.probable_source == "lever"
    assert replay.exists()


def test_tavily_cli_provider_and_credit_metrics(monkeypatch, capsys):
    provider = _provider({"results": []})
    monkeypatch.setattr("radar.discovery.search.tavily.TavilySearchProvider", lambda: provider)
    args = Namespace(
        input=None, provider="tavily", max_queries=2, results_per_query=7, save_results=None
    )

    assert discover_local(args) == 0

    output = capsys.readouterr().out
    assert "Provider: tavily" in output
    assert "Queries executed: 2" in output
    assert "Estimated credits consumed: 2" in output
    assert all(call["payload"]["max_results"] == 7 for call in provider._http.calls)
