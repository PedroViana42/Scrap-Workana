from decimal import Decimal

from radar.database.models.company_source import CompanySourceDB
from radar.database.models.deal import DealDB
from radar.database.models.job import JobDB
from radar.database.models.source import SourceDB
from radar.models.deal import Deal
from radar.models.job import Job
from radar.sources.models import CompanySource, SourceConfig


def source_config_to_values(source: SourceConfig) -> dict:
    return {
        "name": source.name,
        "display_name": source.display_name,
        "content_type": source.content_type.value,
        "status": source.status.value,
        "enabled": source.enabled,
        "collector": source.collector,
        "base_url": source.base_url,
        "interval_minutes": source.interval_minutes,
        "requires_browser": source.requires_browser,
        "requires_auth": source.requires_auth,
        "priority": source.priority,
        "capabilities": source.capabilities.as_dict(),
        "metadata_": dict(source.metadata),
    }


def source_db_to_config(source: SourceDB) -> SourceConfig:
    from radar.sources.models import SourceCapabilities
    from radar.sources.types import ContentType, SourceStatus

    return SourceConfig(
        name=source.name,
        display_name=source.display_name,
        content_type=ContentType(source.content_type),
        status=SourceStatus(source.status),
        enabled=source.enabled,
        collector=source.collector,
        base_url=source.base_url,
        interval_minutes=source.interval_minutes,
        requires_browser=source.requires_browser,
        requires_auth=source.requires_auth,
        priority=source.priority,
        capabilities=SourceCapabilities(**source.capabilities),
        metadata=source.metadata_,
    )


def company_source_to_values(company_source: CompanySource, source_id: int) -> dict:
    return {
        "source_id": source_id,
        "company_name": company_source.company_name,
        "external_identifier": company_source.external_identifier,
        "enabled": company_source.enabled,
        "country": company_source.country,
        "tags": list(company_source.tags),
        "metadata_": dict(company_source.metadata),
    }


def company_source_db_to_domain(company_source: CompanySourceDB) -> CompanySource:
    return CompanySource(
        company_name=company_source.company_name,
        source_name=company_source.source.name,
        external_identifier=company_source.external_identifier,
        enabled=company_source.enabled,
        country=company_source.country,
        tags=tuple(company_source.tags),
        metadata=company_source.metadata_,
    )


def job_to_values(job: Job, source_id: int, fingerprint: str, company_source_id: int | None = None) -> dict:
    return {
        "source_id": source_id,
        "company_source_id": company_source_id,
        "external_id": job.external_id,
        "fingerprint": fingerprint,
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "url": job.url,
        "location": job.location,
        "remote_type": job.remote_type.value,
        "employment_type": job.employment_type.value,
        "seniority": job.seniority.value,
        "salary_min": _decimal_or_none(job.salary_min),
        "salary_max": _decimal_or_none(job.salary_max),
        "salary_currency": job.salary_currency,
        "technologies": job.technologies,
        "published_at": job.published_at,
        "collected_at": job.collected_at,
        "last_seen_at": job.collected_at,
        "active": True,
        "metadata_": job.metadata,
        "raw_data": {},
    }


def deal_to_values(deal: Deal, source_id: int, fingerprint: str) -> dict:
    return {
        "source_id": source_id,
        "external_id": deal.external_id,
        "fingerprint": fingerprint,
        "title": deal.title,
        "description": deal.description,
        "url": deal.url,
        "image_url": deal.image_url,
        "store": deal.store,
        "price": _decimal_or_none(deal.price),
        "original_price": _decimal_or_none(deal.original_price),
        "currency": deal.currency,
        "coupon": deal.coupon,
        "published_at": deal.published_at,
        "collected_at": deal.collected_at,
        "last_seen_at": deal.collected_at,
        "active": True,
        "metadata_": deal.metadata,
        "raw_data": {},
    }


def _decimal_or_none(value: Decimal | int | str | None) -> Decimal | None:
    if value is None or isinstance(value, Decimal):
        return value
    return Decimal(str(value))

