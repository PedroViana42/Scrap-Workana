from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from radar.models.enums import Seniority
from radar.models.job import Job
from radar.relevance.models import RelevanceResult, band_for_score
from radar.relevance.profiles import JobRelevanceProfile, TECH_EARLY_CAREER_BR_PROFILE
from radar.relevance.signals import (
    LocationCategory,
    RoleConfidence,
    detect_experience,
    detect_location,
    detect_role_signal,
    detect_seniority_signals,
    freshness_days,
)
from radar.relevance.technology import detect_technologies


def score_job(
    job: Job,
    profile: JobRelevanceProfile = TECH_EARLY_CAREER_BR_PROFILE,
    now: datetime | None = None,
) -> RelevanceResult:
    now = now or datetime.now(timezone.utc)
    positive: list[str] = []
    negative: list[str] = []

    role_score, roles, role_confidence, role_reasons = _score_role(job, profile)
    positive.extend(role_reasons["positive"])
    negative.extend(role_reasons["negative"])

    seniority_score, seniority_signals, seniority_flags, seniority_reasons = _score_seniority(job, profile)
    positive.extend(seniority_reasons["positive"])
    negative.extend(seniority_reasons["negative"])

    location_score, location_signals, location_category, location_reasons = _score_location(job, profile)
    positive.extend(location_reasons["positive"])
    negative.extend(location_reasons["negative"])

    technology_score, technologies, technology_reasons = _score_technology(job, profile)
    positive.extend(technology_reasons)

    freshness_score, freshness_reason = _score_freshness(job, profile, now)
    if freshness_reason:
        positive.append(freshness_reason)

    components = {
        "role": role_score,
        "seniority": seniority_score,
        "location": location_score,
        "technology": technology_score,
        "freshness": freshness_score,
    }
    score = sum(components.values())

    caps = _caps(role_confidence, seniority_flags, location_category, job)
    for cap, reason in caps:
        if score > cap:
            score = cap
        negative.append(reason)

    score = max(0, min(100, int(round(score))))
    job.technologies = technologies

    return RelevanceResult(
        score=score,
        band=band_for_score(score),
        profile=profile.name,
        version=profile.version,
        positive_reasons=sorted(set(positive)),
        negative_reasons=sorted(set(negative)),
        matched_roles=roles,
        matched_technologies=technologies,
        matched_location_signals=location_signals,
        matched_seniority_signals=seniority_signals,
        components=components,
    )


def _score_role(job: Job, profile: JobRelevanceProfile) -> tuple[int, list[str], RoleConfidence, dict[str, list[str]]]:
    signal = detect_role_signal(job)
    reasons = {"positive": [], "negative": []}
    weights = {
        "BACKEND": 25,
        "DATA_ENGINEERING": 25,
        "AI_ML": 25,
        "SOFTWARE": 23,
        "AUTOMATION": 23,
        "FULLSTACK": 21,
        "DEVOPS_PLATFORM": 20,
        "DATA_ANALYST": 15,
        "BUSINESS_ANALYST": 8,
        "FRONTEND": 13,
        "QA": 14,
        "SECURITY": 17,
    }

    if signal.confidence is RoleConfidence.NON_TECH:
        reasons["negative"].append("Non-tech or business-control title")
        if signal.description_evidence:
            reasons["negative"].append("Technical terms appear only outside the title")
        return 0, signal.families, signal.confidence, reasons

    if signal.confidence is RoleConfidence.TECH_ADJACENT:
        score = max((weights.get(role, 0) for role in signal.title_evidence), default=10)
        score = min(score, 13)
        reasons["negative"].append("Tech-adjacent or management/risk title")
        if signal.title_evidence:
            reasons["positive"].append(f"{signal.title_evidence[0].replace('_', ' ').title()} title signal")
        return min(score, profile.role_max), signal.families, signal.confidence, reasons

    if signal.confidence is RoleConfidence.AMBIGUOUS:
        score = max((weights.get(role, 0) for role in signal.description_evidence), default=8)
        reasons["negative"].append("No clear technical role signal in title")
        return min(score, 10), signal.families, signal.confidence, reasons

    score = max((weights.get(role, 0) for role in signal.title_evidence), default=5)
    if signal.title_evidence:
        reasons["positive"].append(f"{signal.title_evidence[0].replace('_', ' ').title()} role")
    return min(score, profile.role_max), signal.families, signal.confidence, reasons


def _score_seniority(job: Job, profile: JobRelevanceProfile) -> tuple[int, list[str], dict[str, bool], dict[str, list[str]]]:
    signals, extreme = detect_seniority_signals(job)
    signal_set = set(signals)
    reasons = {"positive": [], "negative": []}
    flags = {
        "intern": bool({"intern", "internship", "estagio", "trainee"} & signal_set) or job.seniority is Seniority.INTERN,
        "extreme": extreme,
        "staff_lead": bool({"staff", "principal", "lead"} & signal_set),
        "director": bool({"director", "head", "vp"} & signal_set),
        "manager": "manager" in signal_set,
        "senior": bool({"senior", "sr", "master", "specialist"} & signal_set) or job.seniority is Seniority.SENIOR,
        "level_ii_or_iii": bool({"engineer ii", "engineer iii", "level 2", "level ii", "level 3", "level iii"} & signal_set),
        "experience_3_plus": False,
        "experience_5_plus": False,
    }
    score = 16

    early_terms = {
        "intern",
        "internship",
        "apprentice",
        "estagio",
        "trainee",
        "junior",
        "jr",
        "entry level",
        "entry-level",
        "early career",
        "new grad",
        "graduate",
        "associate",
        "level 1",
        "level i",
        "engineer i",
        "software engineer i",
    }
    if job.seniority in {Seniority.INTERN, Seniority.JUNIOR} or signal_set & early_terms:
        score = 25
        reasons["positive"].append("Early-career title")
    elif job.seniority is Seniority.MID or signal_set & {"mid", "mid-level", "pleno", "engineer ii", "engineer iii"}:
        score = 13 if flags["level_ii_or_iii"] else 17
        if flags["level_ii_or_iii"]:
            reasons["negative"].append("Level II/III title")
        else:
            reasons["positive"].append("Mid-level role can still be relevant")
    elif flags["director"]:
        score = 0
        reasons["negative"].append("Director/head/VP title")
    elif flags["manager"]:
        score = 2
        reasons["negative"].append("Manager-level title")
    elif flags["staff_lead"]:
        score = 3
        reasons["negative"].append("Staff/principal/lead title")
    elif flags["senior"]:
        score = 8
        reasons["negative"].append("Senior-level role")
    else:
        reasons["positive"].append("No explicit seniority requirement")

    experience = detect_experience(job.description)
    if experience.years is not None:
        if experience.years <= 1:
            score = min(profile.seniority_max, score + 5)
            reasons["positive"].append(f"Early-career experience requirement: {experience.phrase}")
        elif experience.years == 2:
            score = min(profile.seniority_max, score + 2)
            reasons["positive"].append(f"Compatible experience requirement: {experience.phrase}")
        elif experience.years >= 5:
            score = max(0, score - 15)
            flags["experience_3_plus"] = True
            flags["experience_5_plus"] = True
            reasons["negative"].append(f"Requires {experience.years}+ years experience")
        elif experience.years >= 3:
            score = max(0, score - (8 if experience.years == 3 else 10))
            flags["experience_3_plus"] = True
            reasons["negative"].append(f"Requires {experience.years}+ years experience")

    return min(score, profile.seniority_max), signals, flags, reasons


def _score_location(job: Job, profile: JobRelevanceProfile) -> tuple[int, list[str], LocationCategory, dict[str, list[str]]]:
    signal = detect_location(job)
    reasons = {"positive": [], "negative": []}
    if signal.category is LocationCategory.BRAZIL:
        score = 20
        reasons["positive"].append("Brazil eligible")
    elif signal.category is LocationCategory.LATAM_INCLUDING_BRAZIL:
        score = 18
        reasons["positive"].append("LATAM includes Brazil")
    elif signal.category is LocationCategory.AMERICAS:
        score = 16
        reasons["positive"].append("Americas remote")
    elif signal.category is LocationCategory.GLOBAL:
        score = 18
        reasons["positive"].append("Worldwide/global remote")
    elif signal.category is LocationCategory.REMOTE_UNSCOPED:
        score = 11
        reasons["positive"].append("Remote role, geography unknown")
    elif signal.category is LocationCategory.FOREIGN_COMPATIBLE_UNKNOWN:
        score = 8
        reasons["negative"].append("Foreign location, Brazil eligibility unknown")
    elif signal.category is LocationCategory.BRAZIL_EXCLUDED:
        score = 0
        reasons["negative"].extend(signal.exclusions)
    elif signal.category is LocationCategory.FOREIGN_RESTRICTED:
        score = 1
        reasons["negative"].extend(signal.exclusions)
    elif signal.category is LocationCategory.FOREIGN_ONSITE:
        score = 0
        reasons["negative"].extend(signal.exclusions)
    else:
        score = 7
        reasons["negative"].append("Location eligibility unclear")
    return min(score, profile.location_max), signal.signals, signal.category, reasons


def _score_technology(job: Job, profile: JobRelevanceProfile) -> tuple[int, list[str], list[str]]:
    detected = detect_technologies(job.title, job.description)
    technologies = sorted(set(job.technologies + detected))
    weights = {
        **profile.complementary_technologies,
        **profile.good_technologies,
        **profile.high_priority_technologies,
    }
    values = sorted((weights.get(tech, 0) for tech in technologies), reverse=True)
    score = 0.0
    multiplier = 1.0
    for value in values:
        score += value * multiplier
        multiplier *= 0.6
    reasons = [f"Matched {tech}" for tech in technologies if weights.get(tech, 0) > 0]
    return min(profile.technology_max, ceil(score)), technologies, reasons


def _score_freshness(job: Job, profile: JobRelevanceProfile, now: datetime) -> tuple[int, str | None]:
    days = freshness_days(job, now)
    if days is None:
        return 3, None
    if days <= 3:
        return profile.freshness_max, "Fresh posting"
    if days <= 7:
        return 8, "Recent posting"
    if days <= 14:
        return 5, "Moderately recent posting"
    if days <= 30:
        return 2, None
    return 0, None


def _caps(
    role_confidence: RoleConfidence,
    seniority_flags: dict[str, bool],
    location_category: LocationCategory,
    job: Job,
) -> list[tuple[int, str]]:
    caps = []
    if role_confidence is RoleConfidence.NON_TECH:
        caps.append((24, "Non-tech role"))
    if role_confidence is RoleConfidence.TECH_ADJACENT:
        caps.append((54, "Tech-adjacent role cap"))
    if role_confidence is RoleConfidence.AMBIGUOUS:
        caps.append((60, "Ambiguous title role cap"))
    if seniority_flags["intern"]:
        caps.append((94, "Internship/trainee calibration cap"))
    if location_category is LocationCategory.FOREIGN_RESTRICTED:
        caps.append((55, "Role explicitly limited outside Brazil eligibility"))
        if role_confidence is RoleConfidence.TECH_ADJACENT:
            caps.append((49, "Foreign tech-adjacent role"))
        if seniority_flags["staff_lead"]:
            caps.append((39, "Foreign staff/principal/lead role"))
    if location_category is LocationCategory.FOREIGN_ONSITE:
        caps.append((35, "Foreign on-site role"))
    if location_category is LocationCategory.BRAZIL_EXCLUDED:
        caps.append((39, "Role explicitly excludes Brazil"))
    if seniority_flags["director"]:
        caps.append((35, "Director/head/VP role"))
    elif seniority_flags["manager"]:
        caps.append((55, "Manager-level role"))
    elif seniority_flags["staff_lead"]:
        caps.append((55, "Staff/principal/lead-level position"))
    elif seniority_flags["senior"] or job.seniority is Seniority.SENIOR:
        caps.append((65, "Senior-level role"))
    if seniority_flags["experience_5_plus"]:
        caps.append((55, "High experience requirement"))
    elif seniority_flags["experience_3_plus"]:
        caps.append((74, "Experience requirement above early-career target"))
    return caps
