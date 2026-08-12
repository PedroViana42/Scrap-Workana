from datetime import datetime, timezone

from radar.collectors.base import BaseCollector, CollectedJob, CollectorResult
from radar.collectors.errors import CollectorHTTPError
from radar.collectors.registry import CollectorRegistry
from radar.models.job import Job
from radar.services.company_validation import validate_company
from radar.sources.models import CompanySource


class FakeOKCollector(BaseCollector[CollectorResult]):
    source_name = "greenhouse"

    def __init__(self, company_source):
        self.company_source = company_source

    def collect(self):
        return CollectorResult(
            source_name="greenhouse",
            company_source=self.company_source,
            jobs=[
                CollectedJob(
                    job=Job(
                        source="greenhouse",
                        external_id="1",
                        title="Junior Software Engineer",
                        company=self.company_source.company_name,
                        url="https://example.com",
                        location="Remote - Brazil",
                        collected_at=datetime.now(timezone.utc),
                    ),
                    raw_data={"id": 1},
                )
            ],
        )


class FakeFailCollector(FakeOKCollector):
    def collect(self):
        raise CollectorHTTPError("HTTP 404")


def _registry(collector):
    registry = CollectorRegistry()
    registry.register("greenhouse", collector)
    return registry


def test_validate_company_http_200_with_mocked_collector():
    result = validate_company(
        CompanySource("Example", "greenhouse", "example"),
        registry=_registry(FakeOKCollector),
    )

    assert result.valid is True
    assert result.jobs_count == 1
    assert result.analysis.jobs_brazil == 1
    assert result.analysis.jobs_remote == 1
    assert result.analysis.jobs_tech == 1
    assert result.analysis.jobs_early_career == 1


def test_validate_company_http_404_with_mocked_collector():
    result = validate_company(
        CompanySource("Example", "greenhouse", "example"),
        registry=_registry(FakeFailCollector),
    )

    assert result.valid is False
    assert "HTTP 404" in result.error

