from radar.collectors.base import BaseCollector


class CollectorNotFoundError(KeyError):
    pass


class CollectorAlreadyRegisteredError(ValueError):
    pass


class CollectorRegistry:
    def __init__(self) -> None:
        self._collectors: dict[str, type[BaseCollector]] = {}

    def register(self, name: str, collector_cls: type[BaseCollector]) -> None:
        normalized_name = self._normalize_name(name)
        if normalized_name in self._collectors:
            raise CollectorAlreadyRegisteredError(
                f"Collector already registered: {normalized_name}"
            )
        self._collectors[normalized_name] = collector_cls

    def get(self, name: str) -> type[BaseCollector]:
        normalized_name = self._normalize_name(name)
        try:
            return self._collectors[normalized_name]
        except KeyError as exc:
            raise CollectorNotFoundError(
                f"Collector not registered: {normalized_name}"
            ) from exc

    def list_available(self) -> list[str]:
        return sorted(self._collectors)

    def has(self, name: str) -> bool:
        return self._normalize_name(name) in self._collectors

    def _normalize_name(self, name: str) -> str:
        return name.lower().strip()


def create_default_registry() -> CollectorRegistry:
    from radar.collectors.jobs.ashby import AshbyCollector
    from radar.collectors.jobs.greenhouse import GreenhouseCollector
    from radar.collectors.jobs.lever import LeverCollector

    registry = CollectorRegistry()
    registry.register(GreenhouseCollector.source_name, GreenhouseCollector)
    registry.register(LeverCollector.source_name, LeverCollector)
    registry.register(AshbyCollector.source_name, AshbyCollector)
    return registry


default_registry = create_default_registry()
