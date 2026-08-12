from radar.sources.company_catalog import get_company_catalog
from radar.sources.models import CompanySource


def list_company_sources(source_name: str | None = None) -> list[CompanySource]:
    return get_company_catalog(source_name)
