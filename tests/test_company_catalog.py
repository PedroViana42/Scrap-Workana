from collections import Counter

from radar.sources.company_catalog import get_company_catalog


def test_company_catalog_has_unique_source_identifier_pairs():
    companies = get_company_catalog()
    pairs = [(company.source_name, company.external_identifier) for company in companies]

    assert len(pairs) == len(set(pairs))


def test_company_catalog_priorities_are_allowed_values():
    assert {company.metadata["priority"] for company in get_company_catalog()}.issubset({40, 60, 80, 100})


def test_company_catalog_tags_are_known_and_non_empty():
    allowed = {
        "brazil",
        "latam",
        "remote",
        "hybrid",
        "onsite",
        "engineering",
        "backend",
        "frontend",
        "data",
        "ai",
        "ml",
        "devops",
        "cloud",
        "platform",
        "security",
        "qa",
        "early-career",
        "database",
        "healthtech",
    }

    for company in get_company_catalog():
        assert company.tags
        assert set(company.tags).issubset(allowed)


def test_company_catalog_distribution_by_ats():
    counts = Counter(company.source_name for company in get_company_catalog())

    assert counts["greenhouse"] >= 10
    assert counts["lever"] >= 5
    assert counts["ashby"] >= 10

