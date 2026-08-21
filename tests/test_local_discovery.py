import pytest

from radar.discovery.models import ResolutionStatus
from radar.discovery.reporting import load_results
from radar.discovery.resolver import (
    LocalDiscoveryResolver,
    extract_external_id,
    identify_source,
    normalize_url,
)


@pytest.mark.parametrize(
    ("url", "source"),
    [
        ("https://boards.greenhouse.io/acme/jobs/123", "greenhouse"),
        ("https://jobs.lever.co/acme/abc-def-123", "lever"),
        ("https://jobs.ashbyhq.com/acme/abc-def-123", "ashby"),
        ("https://apply.workable.com/acme/j/ABC123", "workable"),
        ("https://jobs.smartrecruiters.com/Acme/abc-def-title", "smartrecruiters"),
        ("https://acme.gupy.io/jobs/123", "gupy"),
        ("https://acme.careers-page.com/jobs/x", "zoho_recruit"),
        ("https://recruit.zohopublic.com/recruit/Portal.na?digest=x", "zoho_recruit"),
        ("https://vagas.solides.com.br/vaga/123", "solides"),
        ("https://acme.pandape.infojobs.com.br/Detail/123", "pandape"),
        ("https://acme.rhgestor.com.br/vagas/1", "rh_gestor"),
        ("https://portaldoestagio.com.br/vaga/1", "portal_do_estagio"),
        ("https://linkedin.com/jobs/view/1", "linkedin"),
        ("https://acme.example/jobs/1", "company_site"),
        ("https://bit.ly/example", "unknown"),
    ],
)
def test_identifies_sources(url, source):
    assert identify_source(url) == source


def test_normalizes_tracking_and_preserves_identity_parameters():
    url = "HTTPS://Jobs.Example.com/vaga/1/?utm_source=x&token=identity&ref=y#apply"
    assert normalize_url(url) == "https://jobs.example.com/vaga/1?token=identity"


def test_invalid_url_is_rejected():
    with pytest.raises(ValueError, match="Invalid public"):
        normalize_url("not-a-url")


def test_invalid_discovery_url_becomes_unknown_and_uses_fingerprint_fallback():
    rows = [
        {"discovered_url": "not-a-url", "observed_title": "Dev", "company": "Acme", "location": "Goiânia"},
        {"discovered_url": "still-not-a-url", "observed_title": "Dev", "company": "Acme", "location": "Goiânia"},
    ]
    report = LocalDiscoveryResolver().resolve_all(rows)
    assert len(report.unique_candidates) == 1
    assert report.unique_candidates[0].canonical_url is None
    assert report.unique_candidates[0].resolution_status == ResolutionStatus.UNKNOWN


def test_linkedin_and_aggregator_resolve_to_official_origin():
    resolver = LocalDiscoveryResolver()
    linkedin = resolver.resolve({
        "discovered_url": "https://linkedin.com/jobs/view/1",
        "resolved_url": "https://acme.careers-page.com/jobs/backend",
        "discovered_via": "linkedin",
    })
    aggregator = resolver.resolve({
        "discovered_url": "https://indeed.com/viewjob?id=2",
        "resolved_url": "https://acme.gupy.io/jobs/123?utm_source=indeed",
        "discovered_via": "aggregator",
    })
    assert linkedin.probable_source == "zoho_recruit"
    assert linkedin.resolution_status == ResolutionStatus.RESOLVED_UNSUPPORTED
    assert aggregator.probable_source == "gupy"
    assert aggregator.external_id == "123"
    assert aggregator.resolution_status == ResolutionStatus.PARTNERSHIP_REQUIRED


def test_external_ids_are_only_extracted_from_known_stable_patterns():
    assert extract_external_id("greenhouse", "https://boards.greenhouse.io/a/jobs/123") == "123"
    assert extract_external_id("workable", "https://apply.workable.com/a/j/AB12CD") == "AB12CD"
    assert extract_external_id("company_site", "https://acme.example/jobs/123") is None


def test_deduplicates_by_id_then_url_and_keeps_distinct_ids():
    rows = [
        {"discovered_url": "https://acme.gupy.io/jobs/123?utm_source=a", "observed_title": "Dev"},
        {"discovered_url": "https://acme.gupy.io/jobs/123?utm_source=b", "observed_title": "Dev"},
        {"discovered_url": "https://acme.gupy.io/jobs/124", "observed_title": "Dev"},
        {"discovered_url": "https://acme.example/jobs/x?ref=a", "observed_title": "QA"},
        {"discovered_url": "https://acme.example/jobs/x?ref=b", "observed_title": "QA"},
    ]
    report = LocalDiscoveryResolver().resolve_all(rows)
    assert report.candidates_found == 5
    assert len(report.unique_candidates) == 3
    assert report.duplicates_removed == 2


def test_discovery_only_and_unknown_states():
    resolver = LocalDiscoveryResolver()
    linkedin = resolver.resolve({"discovered_url": "https://linkedin.com/jobs/view/1"})
    assert linkedin.resolution_status == ResolutionStatus.DISCOVERY_ONLY
    assert linkedin.external_id is None
    unknown = resolver.resolve({"discovered_url": "https://bit.ly/unresolved"})
    assert unknown.resolution_status == ResolutionStatus.UNKNOWN
    assert identify_source(None) == "unknown"


def test_fixture_report_has_expected_resolution_mix():
    rows = load_results(__import__("pathlib").Path("tests/fixtures/local_discovery_results.json"))
    report = LocalDiscoveryResolver().resolve_all(rows)
    assert report.candidates_found == 12
    assert len(report.unique_candidates) == 11
    assert report.statuses[ResolutionStatus.RESOLVED_SUPPORTED.value] == 2
    assert report.statuses[ResolutionStatus.PARTNERSHIP_REQUIRED.value] == 2
    assert report.statuses[ResolutionStatus.DISCOVERY_ONLY.value] == 1


def test_metadata_must_be_an_object():
    with pytest.raises((TypeError, ValueError)):
        LocalDiscoveryResolver().resolve({"discovered_url": "https://x.example/vaga", "metadata": []})
