from datetime import datetime, timedelta, timezone

from radar.models import Job, RemoteType, Seniority
from radar.relevance.models import RelevanceBand
from radar.relevance.scoring import score_job
from radar.relevance.signals import LocationCategory, RoleConfidence, detect_experience, detect_location, detect_role_signal
from radar.relevance.technology import detect_technologies


NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def _job(title, location="", description="", seniority=Seniority.UNKNOWN, days_old=2):
    return Job(
        source="test",
        title=title,
        url="https://example.com",
        location=location,
        description=description,
        seniority=seniority,
        remote_type=RemoteType.UNKNOWN,
        published_at=NOW - timedelta(days=days_old),
    )


def test_case_a_junior_backend_brazil_python_postgres():
    result = score_job(
        _job("Junior Backend Engineer", "Remote Brazil", "Python PostgreSQL APIs. 1 year experience.", Seniority.JUNIOR),
        now=NOW,
    )

    assert result.score >= 90
    assert result.band is RelevanceBand.EXCELLENT
    assert "Matched Python" in result.positive_reasons
    assert "Brazil eligible" in result.positive_reasons


def test_case_b_data_engineering_internship_sao_paulo():
    result = score_job(_job("Data Engineering Internship", "Sao Paulo", "SQL and Python", Seniority.INTERN, days_old=0), now=NOW)

    assert result.score >= 90


def test_case_c_software_engineer_i_remote_worldwide_node_typescript():
    result = score_job(_job("Software Engineer I", "Remote Worldwide", "Node.js and TypeScript", days_old=1), now=NOW)

    assert result.score >= 80


def test_case_d_senior_backend_brazil_five_years_is_capped():
    result = score_job(
        _job("Senior Backend Engineer", "Brazil", "Python. 5+ years experience.", Seniority.SENIOR),
        now=NOW,
    )

    assert 40 <= result.score <= 65
    assert any("Requires 5+ years" in reason for reason in result.negative_reasons)
    assert "Senior-level role" in result.negative_reasons


def test_case_e_staff_platform_us_only_is_low():
    result = score_job(_job("Staff Platform Engineer", "US only", "Kubernetes Python"), now=NOW)

    assert result.score < 40
    assert any("outside Brazil" in reason for reason in result.negative_reasons)


def test_case_f_it_risk_management_specialist_brazil_tech_description_below_55():
    result = score_job(
        _job("IT Risk Management Specialist", "Sao Paulo", "Python, SQL, automation and engineering stakeholders."),
        now=NOW,
    )

    assert result.score < 55
    assert "Tech-adjacent or management/risk title" in result.negative_reasons


def test_case_g_model_risk_specialist_brazil_ml_python_description_below_60():
    result = score_job(_job("Model Risk Specialist", "Sao Paulo", "Machine Learning, Python, SQL."), now=NOW)

    assert result.score < 60
    assert "Tech-adjacent role cap" in result.negative_reasons


def test_case_h_data_analyst_aml_compliance_mexico_below_50():
    result = score_job(_job("Data Analyst, AML & Regulatory Compliance", "Mexico City", "SQL and Python"), now=NOW)

    assert result.score < 50
    assert any("Foreign location" in reason for reason in result.negative_reasons)


def test_case_i_junior_software_engineer_colombia_below_65():
    result = score_job(_job("Junior Software Engineer", "Colombia", "Python and APIs.", Seniority.JUNIOR), now=NOW)

    assert result.score < 65
    assert result.score <= 60


def test_foreign_title_location_wins_over_brazil_boilerplate_description():
    result = score_job(
        _job(
            "Junior Software Engineer",
            "Colombia",
            "Remote team with colleagues in Brazil, LATAM and the United States. Python APIs.",
            Seniority.JUNIOR,
        ),
        now=NOW,
    )

    assert result.score <= 60
    assert any("Foreign location" in reason for reason in result.negative_reasons)


def test_case_j_junior_software_engineer_remote_latam_including_brazil_high():
    result = score_job(_job("Junior Software Engineer", "Remote LATAM including Brazil", "Python APIs", Seniority.JUNIOR), now=NOW)

    assert result.score >= 80
    assert "LATAM includes Brazil" in result.positive_reasons


def test_case_k_developer_master_brazil_ai_capped():
    result = score_job(_job("Developer Master, AI Engineer", "Brazil", "AI, Python, Machine Learning"), now=NOW)

    assert result.score <= 65
    assert "Senior-level role" in result.negative_reasons


def test_case_l_engineering_manager_brazil_capped():
    result = score_job(_job("Engineering Manager", "Brazil", "Python, platform, APIs"), now=NOW)

    assert result.score <= 55
    assert "Manager-level role" in result.negative_reasons


def test_case_m_security_engineer_brazil_is_not_non_tech():
    job = _job("Security Engineer", "Brazil", "Python security automation")
    signal = detect_role_signal(job)
    result = score_job(job, now=NOW)

    assert signal.confidence is RoleConfidence.TECH_EXPLICIT
    assert "Non-tech role" not in result.negative_reasons
    assert result.score >= 70


def test_case_n_cybersecurity_risk_engineer_brazil_is_technical_not_non_tech():
    job = _job("Cybersecurity Risk Engineer", "Brazil", "Python, cloud security, audit automation")
    signal = detect_role_signal(job)
    result = score_job(job, now=NOW)

    assert signal.confidence in {RoleConfidence.TECH_EXPLICIT, RoleConfidence.TECH_ADJACENT}
    assert signal.confidence is not RoleConfidence.NON_TECH
    assert "Non-tech role" not in result.negative_reasons


def test_golden_ranking_order_for_calibration_v1_2():
    jobs = [
        _job("Junior Backend Engineer", "Brazil", "Python PostgreSQL", Seniority.JUNIOR),
        _job("Data Engineering Internship", "Brazil", "Python SQL", Seniority.INTERN),
        _job("Software Engineer I", "Remote Worldwide", "Node.js TypeScript"),
        _job("Backend Engineer", "Brazil", "Python SQL"),
        _job("Junior Frontend", "Brazil", "React TypeScript", Seniority.JUNIOR),
        _job("Senior Backend", "Brazil", "Python. 5+ years experience.", Seniority.SENIOR),
        _job("Junior Software Engineer", "Colombia", "Python", Seniority.JUNIOR),
        _job("IT Risk Management Specialist", "Brazil", "Python SQL compliance"),
        _job("Marketing Manager", "Brazil", "SQL dashboards"),
    ]

    ranked = sorted(((score_job(job, now=NOW).score, job.title) for job in jobs), reverse=True)

    assert [title for _, title in ranked] == [
        "Junior Backend Engineer",
        "Data Engineering Internship",
        "Software Engineer I",
        "Backend Engineer",
        "Junior Frontend",
        "Senior Backend",
        "IT Risk Management Specialist",
        "Junior Software Engineer",
        "Marketing Manager",
    ]


def test_technology_aliases_and_false_positives():
    technologies = detect_technologies("Backend", "postgres nodejs dotnet c sharp large language model")

    assert "PostgreSQL" in technologies
    assert "Node.js" in technologies
    assert ".NET" in technologies
    assert "C#" in technologies
    assert "LLM" in technologies
    assert "React" not in detect_technologies("Role", "We need proactive people")


def test_location_signals_latam_remote_and_foreign_restrictions():
    included = detect_location(_job("Engineer", "Remote LATAM including Brazil", ""))
    excluded = detect_location(_job("Engineer", "Remote LATAM excluding Brazil", ""))
    colombia = detect_location(_job("Engineer", "Remote Colombia", ""))
    worldwide = detect_location(_job("Engineer", "Remote Worldwide", ""))
    unknown_remote = detect_location(_job("Engineer", "Remote", ""))

    assert included.category is LocationCategory.LATAM_INCLUDING_BRAZIL
    assert excluded.category is LocationCategory.BRAZIL_EXCLUDED
    assert colombia.category is LocationCategory.FOREIGN_RESTRICTED
    assert worldwide.category is LocationCategory.GLOBAL
    assert unknown_remote.category is LocationCategory.REMOTE_UNSCOPED


def test_experience_detection_and_freshness_are_deterministic():
    assert detect_experience("Minimum 3 years of experience").years == 3
    zero_to_two = detect_experience("Required: 0-2 years experience")
    assert zero_to_two.years == 0
    assert zero_to_two.maximum_years == 2
    assert detect_experience("At least 10+ years of experience").years == 10
    assert detect_experience("Our team has 10 years building APIs").years is None
    old = score_job(_job("Backend Engineer", "Brazil", "Python", days_old=40), now=NOW)
    new = score_job(_job("Backend Engineer", "Brazil", "Python", days_old=1), now=NOW)

    assert new.components["freshness"] > old.components["freshness"]
    assert score_job(_job("Backend Engineer", "Brazil", "Python", days_old=1), now=NOW).score == new.score


def test_junior_software_engineer_is_early_career_but_engineer_ii_is_not():
    junior = score_job(_job("Junior Software Engineer", "Brazil", "Python APIs"), now=NOW)
    level_two = score_job(_job("Software Engineer II", "Brazil", "Python APIs"), now=NOW)

    assert "Early-career title" in junior.positive_reasons
    assert "Early-career title" not in level_two.positive_reasons
    assert "Level II/III title" in level_two.negative_reasons
    assert "engineer i" not in level_two.matched_seniority_signals


def test_senior_software_engineer_has_senior_signal_and_cap():
    result = score_job(_job("Senior Software Engineer", "Brazil", "Python APIs"), now=NOW)

    assert "Senior-level role" in result.negative_reasons
    assert result.score <= 65


def test_explicit_experience_requirements_are_contextual_and_weighted():
    three = score_job(_job("Software Engineer", "Brazil", "3+ years in a backend role. Python."), now=NOW)
    five = score_job(_job("Software Engineer", "Brazil", "At least 5 years of experience. Python."), now=NOW)

    assert detect_experience("3+ years in a backend role").years == 3
    assert detect_experience("Minimum 3 years of experience").years == 3
    assert detect_experience("2-4 years of experience").years == 2
    assert detect_experience("3 to 5 years of experience").years == 3
    assert detect_experience("mínimo 3 anos de experiência").years == 3
    assert detect_experience("The product has operated for 12 years").years is None
    assert detect_experience("With 30 years of experience in digital transformation").years is None
    assert "Requires 3+ years experience" in three.negative_reasons
    assert "Requires 5+ years experience" in five.negative_reasons
    assert five.score < three.score


def test_brazil_remote_brazil_latam_worldwide_and_americas_are_eligible():
    cases = [
        (_job("Software Engineer", "Brazil", "Python"), LocationCategory.BRAZIL, "Brazil eligible"),
        (_job("Software Engineer", "Remote - Brazil", "Python"), LocationCategory.BRAZIL, "Brazil eligible"),
        (_job("Software Engineer", "Remote LATAM", "Python"), LocationCategory.LATAM_INCLUDING_BRAZIL, "LATAM includes Brazil"),
        (_job("Software Engineer", "Remote Americas", "Python"), LocationCategory.AMERICAS, "Americas remote"),
        (_job("Software Engineer", "Worldwide Remote", "Python"), LocationCategory.GLOBAL, "Worldwide/global remote"),
    ]

    for job, category, reason in cases:
        assert detect_location(job).category is category
        assert reason in score_job(job, now=NOW).positive_reasons


def test_remote_restrictions_and_unclear_remote_are_not_brazil_eligible():
    us_only = score_job(_job("Software Engineer", "Remote - US", "Python"), now=NOW)
    europe_only = score_job(_job("Software Engineer", "Europe only", "Python"), now=NOW)
    generic = score_job(_job("Software Engineer", "Remote", "Python"), now=NOW)

    assert detect_location(_job("Software Engineer", "Remote - US", "")).category is LocationCategory.FOREIGN_RESTRICTED
    assert "Foreign location with remote eligibility restricted" in us_only.negative_reasons or "remote - us" in us_only.negative_reasons
    assert "europe only" in europe_only.negative_reasons
    assert detect_location(_job("Software Engineer", "Remote", "")).category is LocationCategory.REMOTE_UNSCOPED
    assert "Remote role, geography unknown" in generic.positive_reasons
    assert "Worldwide/global remote" not in generic.positive_reasons


def test_foreign_on_site_and_global_boilerplate_do_not_imply_worldwide_remote():
    job = _job(
        "Software Engineer II",
        "Ireland",
        "Work autonomously in a globally distributed team. 3+ years in a full-stack role. Python React TypeScript.",
    )
    result = score_job(job, now=NOW)

    assert detect_location(job).category is LocationCategory.FOREIGN_ONSITE
    assert "Worldwide/global remote" not in result.positive_reasons
    assert "Foreign location: on-site outside Brazil" in result.negative_reasons
    assert "Requires 3+ years experience" in result.negative_reasons
    assert "Early-career title" not in result.positive_reasons
    assert result.score <= 35


def test_worldwide_location_is_global_but_product_boilerplate_is_not():
    worldwide = _job("Junior Software Engineer", "Home based - Worldwide", "Python")
    boilerplate = _job(
        "Software Engineer Intern",
        "San Francisco, CA",
        "Our product helps teams work together from anywhere in the world. Python.",
    )

    assert detect_location(worldwide).category is LocationCategory.GLOBAL
    assert detect_location(boilerplate).category is LocationCategory.FOREIGN_ONSITE
