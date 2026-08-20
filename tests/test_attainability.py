from datetime import datetime, timezone

import pytest

from radar.models import Job, RemoteType
from radar.relevance.attainability import classify_attainability, detect_experience_requirements
from radar.relevance.models import AttainabilityLevel
from radar.relevance.scoring import score_job


NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)


def _job(title: str, description: str, location: str = "Brazil Remote") -> Job:
    return Job(
        source="test",
        title=title,
        description=description,
        location=location,
        url="https://example.com/job",
        remote_type=RemoteType.REMOTE,
        collected_at=NOW,
    )


@pytest.mark.parametrize(
    ("job", "reason"),
    [
        (_job("Backend Developer Junior", "0-1 years of experience. Python APIs."), "Explicit junior role"),
        (_job("Software Engineering Intern", "No previous professional experience required.", "Goiânia"), "Internship role"),
        (_job("Graduate Software Engineer", "Recent graduates welcome.", "Worldwide"), "Graduate role"),
    ],
)
def test_high_attainability_cases(job, reason):
    result = classify_attainability(job)

    assert result.level is AttainabilityLevel.HIGH
    assert reason in result.positive


@pytest.mark.parametrize(
    "job",
    [
        _job("Software Engineer", "2-3 years of experience."),
        _job("Mid-Level Developer", "1-2 years of experience. Mentorship available."),
        _job("Software Engineer II", "2 years of experience."),
    ],
)
def test_medium_attainability_cases(job):
    assert classify_attainability(job).level is AttainabilityLevel.MEDIUM


@pytest.mark.parametrize(
    ("job", "expected_reason"),
    [
        (_job("Senior Backend Engineer", "5+ years of experience."), "Senior-level title"),
        (
            _job("Software Engineer II", "Minimum 3 years of experience. Own production services and join the on-call rotation."),
            "Independent production ownership",
        ),
        (_job("Staff Engineer", "Provide technical leadership and mentor engineers."), "Senior-level title"),
        (_job("Mid-Level Software Engineer", "4+ years of experience and independent ownership."), "4+ years experience"),
    ],
)
def test_low_attainability_cases(job, expected_reason):
    result = classify_attainability(job)

    assert result.level is AttainabilityLevel.LOW
    assert expected_reason in result.negative


def test_required_experience_is_stronger_than_preferred_experience():
    preferred = classify_attainability(_job("Mid-Level Software Engineer", "3 years of experience preferred. Mentorship available."))
    required = classify_attainability(_job("Mid-Level Software Engineer", "Minimum 3 years of experience required. Mentorship available."))

    assert preferred.level is AttainabilityLevel.MEDIUM
    assert required.level is AttainabilityLevel.LOW
    assert "3+ years experience preferred" in preferred.warnings
    assert "3+ years experience" in required.warnings


def test_engineer_ii_with_role_experience_and_production_ownership_is_low():
    result = classify_attainability(
        _job(
            "Software Engineer II",
            "3+ years in a full-stack or frontend role. Maintain production services independently and join the on-call rotation.",
        )
    )

    assert result.level is AttainabilityLevel.LOW
    assert "3+ years experience" in result.warnings
    assert "Independent production ownership" in result.negative


def test_experience_detection_supports_ranges_and_portuguese():
    requirements = detect_experience_requirements(
        "Requisito: 2 a 3 anos de experiência. Nice to have: 5 years of experience preferred."
    )

    assert any(item.minimum == 2 and item.maximum == 3 and not item.preferred for item in requirements)
    assert any(item.minimum == 5 and item.preferred for item in requirements)


def test_experience_detection_supports_required_prefix_and_unicode_range():
    prefixed = detect_experience_requirements("Minimum 3 years required.")
    ranged = detect_experience_requirements("Required: 2–3 years of experience.")

    assert any(item.minimum == 3 and not item.preferred for item in prefixed)
    assert any(item.minimum == 2 and item.maximum == 3 for item in ranged)


def test_technology_names_do_not_reduce_attainability():
    result = classify_attainability(_job("Software Engineer", "Work with Kubernetes, AWS and Kafka."))

    assert result.level is AttainabilityLevel.MEDIUM
    assert not result.negative


def test_isolated_code_review_does_not_reduce_attainability():
    result = classify_attainability(_job("Junior Software Engineer", "Participate in code review with the team."))

    assert result.level is AttainabilityLevel.HIGH
    assert not result.negative


def test_score_result_exposes_attainability_without_changing_score_components():
    result = score_job(_job("Junior Backend Engineer", "0-1 years of experience. Python."), now=NOW)

    assert result.attainability is not None
    assert result.attainability.level is AttainabilityLevel.HIGH
    assert result.version == "tech_early_career_br:v1.3"
    assert result.reasons_payload()["attainability"]["level"] == "HIGH"
    assert "attainability" not in result.components
