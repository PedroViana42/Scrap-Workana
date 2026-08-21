from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from radar.cli import build_parser, public_job_postings
from radar.http import HTTPClientError, HTTPStatusError
from radar.public_postings.adapter import PublicJobPostingAdapter
from radar.public_postings.models import PostingLifecycle, PublicPostingReport
from radar.public_postings.parsing import parse_job_postings


FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)


class FixtureClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, params=None, headers=None, allow_redirects=True):
        self.calls.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        if isinstance(response, FixtureResponse):
            return response
        return FixtureResponse(text=response)


class FixtureResponse:
    def __init__(self, *, text="", status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}


def fixture(name):
    return (FIXTURES / name).read_text()


def adapter_for_page(page="public_job_posting_complete.html"):
    return PublicJobPostingAdapter("portaldoestagio.com.br", client=FixtureClient({})), fixture(page)


def test_parses_direct_job_posting_and_sanitizes_description():
    adapter, html = adapter_for_page()
    post = adapter.parse_page("https://portaldoestagio.com.br/vaga/4154/", html, now=NOW)

    assert post.external_id == "4154"
    assert post.canonical_url == "https://portaldoestagio.com.br/vaga/4154"
    assert post.title == "Estágio em Desenvolvimento"
    assert post.description == "Atividades\nApoiar APIs."
    assert "alert" not in post.description and "bad" not in post.description
    assert post.company is None
    assert post.metadata["intermediary_hiring_organization"]["name"] == "Portal do Estágio"
    assert post.apply_url == "https://forms.gle/example"
    assert post.direct_apply is True
    assert post.lifecycle == PostingLifecycle.ACTIVE
    assert post.base_salary["currency"] == "BRL"
    assert post.job_location_type == "TELECOMMUTE"


def test_double_encoded_entities_are_normalized():
    adapter, html = adapter_for_page()
    html = html.replace("Estágio em Desenvolvimento", "Estágio em TI &amp;#8211; 4154")
    post = adapter.parse_page("https://portaldoestagio.com.br/vaga/4154/", html, now=NOW)
    assert post.title == "Estágio em TI – 4154"


def test_parses_graph_and_array_job_postings():
    postings, _, invalid = parse_job_postings(fixture("public_job_posting_graph.html"))
    assert [posting["title"] for posting in postings] == ["Estágio TI", "Second posting"]
    assert invalid == 0


def test_invalid_json_ld_and_missing_job_posting_are_rejected():
    adapter, _ = adapter_for_page()
    with pytest.raises(ValueError, match="does not contain"):
        adapter.parse_page("https://portaldoestagio.com.br/vaga/1/", '<script type="application/ld+json">{bad</script>')
    with pytest.raises(ValueError, match="does not contain"):
        adapter.parse_page("https://portaldoestagio.com.br/vaga/1/", "<html></html>")


def test_canonical_must_remain_allowlisted_and_job_shaped():
    adapter, html = adapter_for_page()
    external = html.replace(
        "https://portaldoestagio.com.br/vaga/4154/?utm_source=test",
        "https://evil.example/vaga/4154/",
    )
    post = adapter.parse_page("https://portaldoestagio.com.br/vaga/4154/", external, now=NOW)
    assert post.canonical_url == "https://portaldoestagio.com.br/vaga/4154"
    with pytest.raises(ValueError, match="outside"):
        adapter.parse_page("https://127.0.0.1/vaga/4154/", html)
    with pytest.raises(ValueError, match="job path"):
        adapter.parse_page("https://portaldoestagio.com.br/not-a-job/", html)


def test_identifier_mismatch_is_reported_as_invalid():
    adapter, html = adapter_for_page()
    html = html.replace('"value": "4154"', '"value": "9999"')
    post = adapter.parse_page("https://portaldoestagio.com.br/vaga/4154/", html, now=NOW)
    assert post.external_id is None
    assert post.lifecycle == PostingLifecycle.INVALID
    assert post.metadata["issues"] == ["external_id_mismatch:url=4154,identifier=9999"]


@pytest.mark.parametrize(
    ("valid_through", "expected"),
    [
        ('"2026-08-20T00:00:00Z"', PostingLifecycle.EXPIRED),
        ('"2026-09-20T00:00:00Z"', PostingLifecycle.ACTIVE),
        (None, PostingLifecycle.ACTIVE),
    ],
)
def test_lifecycle(valid_through, expected):
    adapter, html = adapter_for_page()
    if valid_through is None:
        html = html.replace('"validThrough": "2026-10-13T23:59:59-03:00",', "")
    else:
        html = html.replace('"2026-10-13T23:59:59-03:00"', valid_through)
    post = adapter.parse_page("https://portaldoestagio.com.br/vaga/4154/", html, now=NOW)
    assert post.lifecycle == expected


def test_non_intermediary_organization_is_preserved_as_company():
    adapter, html = adapter_for_page()
    html = html.replace('"name": "Portal do Estágio"', '"name": "Empresa Exemplo"')
    post = adapter.parse_page("https://portaldoestagio.com.br/vaga/4154/", html, now=NOW)
    assert post.company == "Empresa Exemplo"


def test_sitemap_index_filters_job_urls_and_external_hosts():
    index = fixture("public_job_posting_sitemap_index.xml")
    urlset = fixture("public_job_posting_urlset.xml")
    client = FixtureClient({
        "https://portaldoestagio.com.br/sitemap_index.xml": index,
        "https://portaldoestagio.com.br/job_listing-sitemap.xml": urlset,
    })
    adapter = PublicJobPostingAdapter("portaldoestagio.com.br", client=client)

    assert adapter.discover_urls(limit=20) == [
        "https://portaldoestagio.com.br/vaga/4154",
        "https://www.portaldoestagio.com.br/vaga/4053",
    ]
    assert "https://evil.example/jobs.xml" not in client.calls


def test_run_honors_limit_and_marks_http_failures_invalid():
    index = fixture("public_job_posting_sitemap_index.xml")
    urlset = fixture("public_job_posting_urlset.xml")
    html = fixture("public_job_posting_complete.html")
    client = FixtureClient({
        "https://portaldoestagio.com.br/sitemap_index.xml": index,
        "https://portaldoestagio.com.br/job_listing-sitemap.xml": urlset,
        "https://portaldoestagio.com.br/vaga/4154": html,
        "https://www.portaldoestagio.com.br/vaga/4053": HTTPStatusError(404, "https://www.portaldoestagio.com.br/vaga/4053"),
    })
    report = PublicJobPostingAdapter("portaldoestagio.com.br", client=client).run(limit=2, now=NOW)
    assert report.urls_discovered == 2
    assert report.valid == 1
    assert report.invalid == 1
    assert report.requests == 4


@pytest.mark.parametrize("limit", [0, 21])
def test_limit_is_conservative(limit):
    with pytest.raises(ValueError, match="between 1 and 20"):
        PublicJobPostingAdapter("portaldoestagio.com.br", client=FixtureClient({})).run(limit=limit)


def test_non_allowlisted_domain_is_rejected():
    with pytest.raises(ValueError, match="not allowlisted"):
        PublicJobPostingAdapter("example.com")


def test_redirect_is_validated_before_following_to_prevent_ssrf():
    client = FixtureClient({
        "https://portaldoestagio.com.br/sitemap_index.xml": FixtureResponse(
            status_code=302, headers={"Location": "http://127.0.0.1/private"}
        ),
    })
    adapter = PublicJobPostingAdapter("portaldoestagio.com.br", client=client)
    with pytest.raises(ValueError, match="outside"):
        adapter.discover_urls(limit=1)
    assert client.calls == ["https://portaldoestagio.com.br/sitemap_index.xml"]


def test_cli_parser_and_read_only_report(capsys):
    args = build_parser().parse_args([
        "public-job-postings", "--domain", "portaldoestagio.com.br", "--limit", "2"
    ])
    assert args.limit == 2
    report = PublicPostingReport(0, 0, (), (), 1)
    with patch("radar.public_postings.adapter.PublicJobPostingAdapter.run", return_value=report):
        assert public_job_postings(args) == 0
    assert "Public JobPosting read-only report" in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    [HTTPClientError("timeout"), HTTPStatusError(429, "https://portaldoestagio.com.br/vaga/1"), HTTPStatusError(500, "https://portaldoestagio.com.br/vaga/1")],
)
def test_http_errors_do_not_escape_run(error):
    index = fixture("public_job_posting_sitemap_index.xml")
    urlset = fixture("public_job_posting_urlset.xml").replace(
        "https://www.portaldoestagio.com.br/vaga/4053/", "https://portaldoestagio.com.br/not-a-job/"
    )
    client = FixtureClient({
        "https://portaldoestagio.com.br/sitemap_index.xml": index,
        "https://portaldoestagio.com.br/job_listing-sitemap.xml": urlset,
        "https://portaldoestagio.com.br/vaga/4154": error,
    })
    report = PublicJobPostingAdapter("portaldoestagio.com.br", client=client).run(limit=1)
    assert report.invalid == 1
