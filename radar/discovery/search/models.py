from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    """Uninterpreted public result returned by a search provider."""

    title: str
    url: str
    snippet: str | None
    query: str
    provider: str
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)
