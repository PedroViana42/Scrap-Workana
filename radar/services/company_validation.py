from dataclasses import dataclass

from radar.collectors.errors import CollectorError
from radar.collectors.registry import CollectorRegistry, default_registry
from radar.services.company_analysis import CompanyBoardAnalysis, analyze_collector_result
from radar.sources.company_catalog import get_company_catalog
from radar.sources.models import CompanySource


@dataclass
class CompanyValidationResult:
    company_source: CompanySource
    valid: bool
    jobs_count: int = 0
    analysis: CompanyBoardAnalysis | None = None
    error: str | None = None
    requests: int = 1


def validate_company(company_source: CompanySource, registry: CollectorRegistry | None = None) -> CompanyValidationResult:
    registry = registry or default_registry
    try:
        collector_cls = registry.get(company_source.source_name)
        result = collector_cls(company_source=company_source).collect()
        analysis = analyze_collector_result(result)
        return CompanyValidationResult(
            company_source=company_source,
            valid=True,
            jobs_count=result.items_found,
            analysis=analysis,
        )
    except CollectorError as exc:
        return CompanyValidationResult(company_source=company_source, valid=False, error=str(exc))


def validate_company_catalog(source_name: str | None = None) -> list[CompanyValidationResult]:
    return [validate_company(company_source) for company_source in get_company_catalog(source_name)]

