from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class PostingLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class PublicJobPosting:
    """Parsed public data for review; deliberately not a persistable Radar Job."""

    source: str
    external_id: str | None
    canonical_url: str
    title: str | None
    description: str | None
    date_posted: datetime | None
    valid_through: datetime | None
    employment_type: str | list[str] | None
    hiring_organization: dict[str, Any] | None
    company: str | None
    location: Any
    applicant_location_requirements: Any
    job_location_type: str | None
    base_salary: Any
    direct_apply: bool | None
    apply_url: str | None
    lifecycle: PostingLifecycle
    raw_json_ld: dict[str, Any] = field(repr=False)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicPostingReport:
    urls_discovered: int
    pages_read: int
    postings: tuple[PublicJobPosting, ...]
    invalid_urls: tuple[str, ...]
    requests: int

    @property
    def valid(self) -> int:
        return sum(post.lifecycle != PostingLifecycle.INVALID for post in self.postings)

    @property
    def active(self) -> int:
        return sum(post.lifecycle == PostingLifecycle.ACTIVE for post in self.postings)

    @property
    def expired(self) -> int:
        return sum(post.lifecycle == PostingLifecycle.EXPIRED for post in self.postings)

    @property
    def invalid(self) -> int:
        return len(self.invalid_urls) + sum(post.lifecycle == PostingLifecycle.INVALID for post in self.postings)
