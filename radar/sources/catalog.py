from radar.sources.models import SourceCapabilities, SourceConfig
from radar.sources.types import ContentType, SourceStatus


_SOURCES = [
    SourceConfig(
        name="greenhouse",
        display_name="Greenhouse",
        content_type=ContentType.JOB,
        collector="greenhouse",
        status=SourceStatus.ACTIVE,
        enabled=True,
        interval_minutes=60,
        capabilities=SourceCapabilities(supports_company_boards=True),
    ),
    SourceConfig(
        name="lever",
        display_name="Lever",
        content_type=ContentType.JOB,
        collector="lever",
        status=SourceStatus.ACTIVE,
        enabled=True,
        interval_minutes=60,
        capabilities=SourceCapabilities(supports_company_boards=True),
    ),
    SourceConfig(
        name="ashby",
        display_name="Ashby",
        content_type=ContentType.JOB,
        collector="ashby",
        status=SourceStatus.ACTIVE,
        enabled=True,
        interval_minutes=60,
        capabilities=SourceCapabilities(supports_company_boards=True),
    ),
    SourceConfig(
        name="workable",
        display_name="Workable",
        content_type=ContentType.JOB,
        collector="workable",
        base_url="https://www.workable.com/api/accounts/{subdomain}",
        status=SourceStatus.ACTIVE,
        enabled=True,
        interval_minutes=60,
        capabilities=SourceCapabilities(
            supports_remote=True,
            supports_published_at=True,
            supports_company_boards=True,
        ),
    ),
    SourceConfig(
        name="remoteok",
        display_name="Remote OK",
        content_type=ContentType.JOB,
        status=SourceStatus.DISABLED,
        capabilities=SourceCapabilities(supports_remote=True, supports_published_at=True),
    ),
    SourceConfig(
        name="weworkremotely",
        display_name="We Work Remotely",
        content_type=ContentType.JOB,
        status=SourceStatus.DISABLED,
        capabilities=SourceCapabilities(supports_remote=True, supports_published_at=True),
    ),
    SourceConfig(
        name="remotive",
        display_name="Remotive",
        content_type=ContentType.JOB,
        status=SourceStatus.DISABLED,
        capabilities=SourceCapabilities(supports_remote=True, supports_published_at=True),
    ),
    SourceConfig(
        name="gupy",
        display_name="Gupy",
        content_type=ContentType.JOB,
        status=SourceStatus.DISABLED,
        capabilities=SourceCapabilities(supports_company_boards=True),
    ),
    SourceConfig(
        name="programathor",
        display_name="ProgramaThor",
        content_type=ContentType.JOB,
        status=SourceStatus.DISABLED,
    ),
    SourceConfig(
        name="smartrecruiters",
        display_name="SmartRecruiters",
        content_type=ContentType.JOB,
        status=SourceStatus.DISABLED,
        capabilities=SourceCapabilities(supports_company_boards=True),
    ),
    SourceConfig(
        name="mercadolivre",
        display_name="Mercado Livre",
        content_type=ContentType.DEAL,
        status=SourceStatus.DISABLED,
    ),
    SourceConfig(
        name="amazon",
        display_name="Amazon",
        content_type=ContentType.DEAL,
        status=SourceStatus.DISABLED,
    ),
    SourceConfig(
        name="kabum",
        display_name="KaBuM!",
        content_type=ContentType.DEAL,
        status=SourceStatus.DISABLED,
    ),
    SourceConfig(
        name="pichau",
        display_name="Pichau",
        content_type=ContentType.DEAL,
        status=SourceStatus.DISABLED,
    ),
]


def list_sources(content_type: ContentType | None = None) -> list[SourceConfig]:
    if content_type is None:
        return list(_SOURCES)
    return [source for source in _SOURCES if source.content_type is content_type]


def get_source(name: str) -> SourceConfig:
    normalized_name = name.lower().strip()
    for source in _SOURCES:
        if source.name == normalized_name:
            return source
    raise KeyError(f"Source not found: {name}")
