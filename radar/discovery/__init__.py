"""Read-only discovery primitives, intentionally separate from job ingestion."""

from radar.discovery.models import DiscoveryCandidate, ResolutionStatus
from radar.discovery.resolver import LocalDiscoveryResolver

__all__ = ["DiscoveryCandidate", "LocalDiscoveryResolver", "ResolutionStatus"]
