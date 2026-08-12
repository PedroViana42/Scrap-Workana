import pytest

from radar.collectors.base import BaseCollector
from radar.collectors.registry import (
    CollectorAlreadyRegisteredError,
    CollectorNotFoundError,
    CollectorRegistry,
    create_default_registry,
)


class ExampleCollector(BaseCollector[str]):
    source_name = "example"

    def collect(self) -> list[str]:
        return ["ok"]


def test_registry_registers_and_resolves_collector():
    registry = CollectorRegistry()
    registry.register("example", ExampleCollector)

    assert registry.get("example") is ExampleCollector
    assert registry.has("EXAMPLE") is True
    assert registry.list_available() == ["example"]


def test_registry_prevents_duplicate_registration():
    registry = CollectorRegistry()
    registry.register("example", ExampleCollector)

    with pytest.raises(CollectorAlreadyRegisteredError):
        registry.register(" example ", ExampleCollector)


def test_registry_reports_missing_collector_clearly():
    registry = CollectorRegistry()

    with pytest.raises(CollectorNotFoundError, match="greenhouse"):
        registry.get("greenhouse")


def test_default_registry_starts_empty_until_collectors_are_implemented():
    registry = create_default_registry()

    assert registry.list_available() == ["ashby", "greenhouse", "lever"]
    assert registry.has("greenhouse") is True
    assert registry.has("remoteok") is False
