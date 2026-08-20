from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class Salary(BaseModel):
    min: Decimal | None = None
    max: Decimal | None = None
    currency: str | None = None


class Attainability(BaseModel):
    level: Literal["HIGH", "MEDIUM", "LOW"]
    positive: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    negative: list[str] = Field(default_factory=list)


class JobListItem(BaseModel):
    id: int
    title: str
    company: str | None
    source: str
    url: str
    location: str | None
    remote: bool
    remote_type: str
    employment_type: str
    seniority: str
    technologies: list[str] = Field(default_factory=list)
    published_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    relevance_score: int | None
    relevance_band: str | None
    attainability: Attainability | None = None


class JobDetail(JobListItem):
    description: str | None
    salary: Salary
    relevance_reasons: dict[str, Any] | None = None


class JobsPage(BaseModel):
    items: list[JobListItem]
    page: int
    page_size: int
    total: int
    pages: int
