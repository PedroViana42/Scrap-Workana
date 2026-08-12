import pytest

from radar.collectors.base import BaseCollector


def test_base_collector_requires_collect_implementation():
    with pytest.raises(TypeError):
        BaseCollector()


def test_base_collector_subclass_collects_items():
    class FakeCollector(BaseCollector[str]):
        source_name = "fake"

        def collect(self) -> list[str]:
            return ["item"]

    collector = FakeCollector()

    assert collector.source_name == "fake"
    assert collector.collect() == ["item"]

