from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from radar.sources.types import ContentType, SourceStatus


@dataclass(frozen=True)
class SourceCapabilities:
    supports_salary: bool = False
    supports_remote: bool = False
    supports_published_at: bool = False
    supports_company_boards: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "supports_salary": self.supports_salary,
            "supports_remote": self.supports_remote,
            "supports_published_at": self.supports_published_at,
            "supports_company_boards": self.supports_company_boards,
        }


@dataclass(frozen=True)
class SourceConfig:
    name: str
    display_name: str
    content_type: ContentType
    collector: str | None = None
    base_url: str | None = None
    interval_minutes: int | None = None
    requires_browser: bool = False
    requires_auth: bool = False
    priority: int = 100
    status: SourceStatus = SourceStatus.DISABLED
    enabled: bool = False
    capabilities: SourceCapabilities = field(default_factory=SourceCapabilities)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class CompanySource:
    company_name: str
    source_name: str
    external_identifier: str
    enabled: bool = True
    country: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

