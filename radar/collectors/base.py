from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from radar.models.job import Job
from radar.sources.models import CompanySource


T = TypeVar("T")


@dataclass
class CollectedJob:
    job: Job
    raw_data: dict


@dataclass
class CollectorResult:
    source_name: str
    company_source: CompanySource
    jobs: list[CollectedJob]
    metadata: dict = field(default_factory=dict)

    @property
    def items_found(self) -> int:
        return len(self.jobs)


class BaseCollector(ABC, Generic[T]):
    source_name: str

    @abstractmethod
    def collect(self) -> list[T]:
        """Collect opportunities from a source."""
