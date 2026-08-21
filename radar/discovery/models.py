from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResolutionStatus(StrEnum):
    RESOLVED_SUPPORTED = "RESOLVED_SUPPORTED"
    RESOLVED_UNSUPPORTED = "RESOLVED_UNSUPPORTED"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    PARTNERSHIP_REQUIRED = "PARTNERSHIP_REQUIRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DiscoveryCandidate:
    """A URL candidate for human review, never a persistable Radar Job."""

    discovered_url: str
    canonical_url: str | None
    observed_title: str | None = None
    company: str | None = None
    location: str | None = None
    discovered_via: str = "unknown"
    probable_source: str = "unknown"
    external_id: str | None = None
    resolution_status: ResolutionStatus = ResolutionStatus.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def deduplication_key(self) -> tuple[str, ...]:
        if self.external_id and self.probable_source != "unknown":
            return ("external_id", self.probable_source, self.external_id.casefold())
        if self.canonical_url:
            return ("canonical_url", self.canonical_url)
        return (
            "fingerprint",
            _token(self.company),
            _token(self.observed_title),
            _token(self.location),
            _token(str(self.metadata.get("modality") or "")),
        )


def _token(value: str | None) -> str:
    return " ".join((value or "").casefold().split())
