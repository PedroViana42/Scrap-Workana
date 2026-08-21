from abc import ABC, abstractmethod

from radar.discovery.search.models import SearchResult


class SearchProviderError(RuntimeError):
    pass


class SearchProviderUnavailable(SearchProviderError):
    pass


class SearchProviderAuthenticationError(SearchProviderError):
    pass


class SearchProviderResponseError(SearchProviderError):
    pass


class SearchProvider(ABC):
    name: str
    requests_made: int
    estimated_cost_per_request_usd: float | None = None

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        count: int,
        country: str,
        language: str,
    ) -> list[SearchResult]:
        raise NotImplementedError
