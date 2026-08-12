from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from radar.models.enums import EmploymentType, RemoteType, Seniority


@dataclass
class Job:
    source: str
    title: str
    url: str
    external_id: str | None = None
    company: str | None = None
    description: str | None = None
    location: str | None = None
    remote_type: RemoteType = RemoteType.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    seniority: Seniority = Seniority.UNKNOWN
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = None
    technologies: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
