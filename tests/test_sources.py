from radar.sources import CompanySource, ContentType, SourceConfig, SourceStatus
from radar.sources.catalog import get_source, list_sources
from radar.sources.companies import list_company_sources


def test_source_config_defaults_are_serializable_and_disabled():
    source = SourceConfig(
        name="example",
        display_name="Example",
        content_type=ContentType.JOB,
    )

    assert source.name == "example"
    assert source.enabled is False
    assert source.status is SourceStatus.DISABLED
    assert source.capabilities.as_dict()["supports_salary"] is False
    assert dict(source.metadata) == {}


def test_content_type_and_source_status_values():
    assert ContentType.JOB.value == "job"
    assert ContentType.DEAL.value == "deal"
    assert SourceStatus.ACTIVE.value == "active"
    assert SourceStatus.LEGACY.value == "legacy"


def test_company_source_keeps_external_identifier_generic():
    company_source = CompanySource(
        company_name="Example Company",
        source_name="greenhouse",
        external_identifier="example-board-id",
        country="BR",
        tags=("tech", "remote"),
    )

    assert company_source.company_name == "Example Company"
    assert company_source.source_name == "greenhouse"
    assert company_source.external_identifier == "example-board-id"
    assert company_source.tags == ("tech", "remote")


def test_company_catalog_starts_empty():
    assert len(list_company_sources()) >= 35
    assert all(source.source_name == "greenhouse" for source in list_company_sources("greenhouse"))


def test_catalog_contains_job_and_deal_sources():
    job_sources = {source.name for source in list_sources(ContentType.JOB)}
    deal_sources = {source.name for source in list_sources(ContentType.DEAL)}

    assert job_sources == {
        "greenhouse",
        "lever",
        "ashby",
        "remoteok",
        "weworkremotely",
        "remotive",
        "gupy",
        "programathor",
        "smartrecruiters",
    }
    assert deal_sources == {"mercadolivre", "amazon", "kabum", "pichau"}


def test_catalog_does_not_contain_workana():
    all_sources = {source.name for source in list_sources()}

    assert "workana" not in all_sources
    try:
        get_source("workana")
    except KeyError as exc:
        assert "workana" in str(exc)
    else:
        raise AssertionError("workana should not be present in the catalog")

def test_planned_sources_are_disabled_and_have_no_collector():
    source_names = {
        "remoteok",
        "weworkremotely",
        "remotive",
        "gupy",
        "programathor",
        "smartrecruiters",
        "mercadolivre",
        "amazon",
        "kabum",
        "pichau",
    }

    for name in source_names:
        source = get_source(name)
        assert source.status is SourceStatus.DISABLED
        assert source.enabled is False
        assert source.collector is None


def test_implemented_ats_sources_are_active_and_registered_by_name():
    for name in ["greenhouse", "lever", "ashby"]:
        source = get_source(name)
        assert source.status is SourceStatus.ACTIVE
        assert source.enabled is True
        assert source.collector == name
