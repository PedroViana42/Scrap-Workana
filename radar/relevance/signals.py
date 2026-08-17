from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
import unicodedata

from radar.models.enums import Seniority
from radar.models.job import Job


class RoleConfidence(str, Enum):
    TECH_EXPLICIT = "TECH_EXPLICIT"
    TECH_ADJACENT = "TECH_ADJACENT"
    AMBIGUOUS = "AMBIGUOUS"
    NON_TECH = "NON_TECH"


class LocationCategory(str, Enum):
    BRAZIL = "BRAZIL"
    LATAM_INCLUDING_BRAZIL = "LATAM_INCLUDING_BRAZIL"
    AMERICAS = "AMERICAS"
    GLOBAL = "GLOBAL"
    REMOTE_UNSCOPED = "REMOTE_UNSCOPED"
    FOREIGN_COMPATIBLE_UNKNOWN = "FOREIGN_COMPATIBLE_UNKNOWN"
    FOREIGN_RESTRICTED = "FOREIGN_RESTRICTED"
    FOREIGN_ONSITE = "FOREIGN_ONSITE"
    BRAZIL_EXCLUDED = "BRAZIL_EXCLUDED"
    UNKNOWN = "UNKNOWN"


BRAZIL_TERMS = [
    "brazil",
    "brasil",
    "sao paulo",
    "rio de janeiro",
    "belo horizonte",
    "bh",
    "curitiba",
    "florianopolis",
    "brasilia",
    "porto alegre",
    "recife",
    "campinas",
    "goiania",
]
LATAM_TERMS = ["latam", "latin america", "latin-american", "south america", "america latina"]
LATAM_INCLUDE_BRAZIL_TERMS = [
    "including brazil",
    "includes brazil",
    "incluindo brasil",
    "inclui brasil",
    "brazil included",
]
AMERICAS_TERMS = ["americas", "north and south america"]
WORLDWIDE_REMOTE_TERMS = [
    "worldwide remote",
    "remote worldwide",
    "global remote",
    "remote globally",
    "work from anywhere",
    "remote anywhere",
]
WORLDWIDE_LOCATION_TERMS = ["worldwide", "global"]
REMOTE_TERMS = ["remote", "remoto", "remota"]
EXCLUSION_TERMS = [
    "us only",
    "u.s. only",
    "usa only",
    "canada only",
    "europe only",
    "emea only",
    "uk only",
    "united states only",
    "remote - us",
    "remote us",
    "remote - usa",
    "remote usa",
    "remote - united states",
    "remote united states",
    "eu only",
    "remote - eu",
    "remote eu",
]
LATAM_EXCLUDING_BRAZIL = ["latam excluding brazil", "latin america excluding brazil", "except brazil", "except brasil"]
FOREIGN_TERMS = [
    "colombia",
    "bogota",
    "mexico",
    "mexico city",
    "ciudad de mexico",
    "argentina",
    "buenos aires",
    "united states",
    "usa",
    " u.s.",
    " us ",
    "palo alto",
    "san francisco",
    "new york",
    "seattle",
    "chicago",
    "canada",
    "uk",
    "united kingdom",
    "germany",
    "spain",
    "portugal",
    "ireland",
    "greece",
    "norway",
    "france",
    "italy",
    "netherlands",
    "sweden",
    "denmark",
    "belgium",
    "switzerland",
    "australia",
    "new zealand",
]

ROLE_FAMILIES = {
    "BACKEND": ["backend", "back-end", "api engineer", "server engineer"],
    "DATA_ENGINEERING": ["data engineer", "data engineering", "analytics engineer", "data platform"],
    "DATA_ANALYST": ["data analyst", "analytics analyst", "bi analyst"],
    "BUSINESS_ANALYST": ["business analyst"],
    "AI_ML": ["machine learning", "ml engineer", "ai engineer", "applied ai", "llm"],
    "SOFTWARE": ["software engineer", "software developer", "developer", "engenheiro de software", "engenheira de software"],
    "AUTOMATION": ["automation engineer", "rpa", "workflow automation"],
    "FULLSTACK": ["full stack", "fullstack"],
    "DEVOPS_PLATFORM": ["platform engineer", "devops", "sre", "site reliability", "infrastructure engineer", "cloud engineer"],
    "FRONTEND": ["frontend", "front-end", "react developer", "web developer"],
    "QA": ["qa engineer", "quality engineer", "test engineer"],
    "SECURITY": [
        "security engineer",
        "security risk engineer",
        "cybersecurity engineer",
        "cybersecurity risk engineer",
        "technology risk engineer",
        "application security",
        "cloud security",
    ],
}

ADJACENT_TITLE_TERMS = [
    "data analyst",
    "business analyst",
    "solutions engineer",
    "solution engineer",
    "sales engineer",
    "technology risk",
    "model risk",
    "it risk",
]
RISK_FINANCE_COMPLIANCE_TERMS = [
    "risk management",
    "enterprise risk",
    "credit risk",
    "model risk",
    "financial risk",
    "aml",
    "anti-money laundering",
    "anti money laundering",
    "regulatory compliance",
    "compliance",
    "fraud",
    "audit",
    "internal controls",
    "finance",
    "accounting",
]
NON_TECH_TITLE_TERMS = [
    "marketing",
    "account executive",
    "sales",
    "recruiter",
    "recruiting",
    "legal",
    "customer success",
    "product manager",
    "product owner",
    "project manager",
    "program manager",
    "designer",
    "design manager",
    "financial analyst",
    "risk analyst",
]
MANAGEMENT_TERMS = ["manager", "director", "head", "vp", "program manager", "project manager", "product manager", "product owner"]
EARLY_TITLE_TERMS = [
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
]
MID_TITLE_TERMS = ["mid", "mid-level", "pleno", "engineer ii", "engineer iii", "level 2", "level ii", "level 3", "level iii"]
SENIOR_TITLE_TERMS = ["senior", "sr", "staff", "principal", "lead", "master", "specialist", "manager", "director", "head", "architect", "vp"]
STAFF_LEAD_TERMS = ["staff", "principal", "lead"]
DIRECTOR_TERMS = ["director", "head", "vp"]
EXTREME_SENIOR_TERMS = STAFF_LEAD_TERMS + DIRECTOR_TERMS + ["manager", "master", "specialist"]


@dataclass(frozen=True)
class ExperienceSignal:
    years: int | None
    phrase: str | None
    maximum_years: int | None = None


@dataclass(frozen=True)
class LocationSignal:
    remote: bool
    brazil_eligible: bool | None
    signals: list[str]
    exclusions: list[str]
    category: LocationCategory = LocationCategory.UNKNOWN


@dataclass(frozen=True)
class RoleSignal:
    families: list[str]
    confidence: RoleConfidence
    title_evidence: list[str]
    description_evidence: list[str]
    risk_finance_compliance: bool
    management: bool


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_value).strip()


def _contains_any(text: str, terms: list[str]) -> bool:
    padded = f" {text} "
    return any(term in padded or term in text for term in terms)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def _matched_families(text: str) -> list[str]:
    return [family for family, terms in ROLE_FAMILIES.items() if any(term in text for term in terms)]


def detect_role_signal(job: Job) -> RoleSignal:
    title = normalize_text(job.title)
    description = normalize_text(job.description)
    title_families = _matched_families(title)
    description_families = [family for family in _matched_families(description) if family not in title_families]
    risk_finance_compliance = _contains_any(title, RISK_FINANCE_COMPLIANCE_TERMS)
    management = _contains_any(title, MANAGEMENT_TERMS)
    explicit_security_risk = ("security" in title or "cybersecurity" in title or "technology" in title) and "engineer" in title

    confidence = RoleConfidence.AMBIGUOUS
    if _contains_any(title, NON_TECH_TITLE_TERMS):
        confidence = RoleConfidence.NON_TECH
    elif risk_finance_compliance and not explicit_security_risk:
        confidence = RoleConfidence.TECH_ADJACENT if _contains_any(title, ADJACENT_TITLE_TERMS) else RoleConfidence.NON_TECH
    elif title_families:
        confidence = RoleConfidence.TECH_ADJACENT if _contains_any(title, ADJACENT_TITLE_TERMS) else RoleConfidence.TECH_EXPLICIT
    elif description_families:
        confidence = RoleConfidence.AMBIGUOUS

    if management and confidence is RoleConfidence.TECH_EXPLICIT:
        confidence = RoleConfidence.TECH_ADJACENT

    return RoleSignal(
        families=sorted(set(title_families + description_families)),
        confidence=confidence,
        title_evidence=title_families,
        description_evidence=description_families,
        risk_finance_compliance=risk_finance_compliance,
        management=management,
    )


def detect_role_families(job: Job) -> tuple[list[str], bool]:
    signal = detect_role_signal(job)
    return signal.families, signal.confidence is RoleConfidence.NON_TECH


def detect_seniority_signals(job: Job) -> tuple[list[str], bool]:
    title = normalize_text(job.title)
    signals = []
    if job.seniority in {Seniority.INTERN, Seniority.JUNIOR}:
        signals.append(job.seniority.value)
    if job.seniority is Seniority.MID:
        signals.append("mid")
    if job.seniority is Seniority.SENIOR:
        signals.append("senior")
    signals.extend(term for term in EARLY_TITLE_TERMS if _contains_phrase(title, term))
    signals.extend(term for term in MID_TITLE_TERMS if _contains_phrase(title, term))
    signals.extend(term for term in SENIOR_TITLE_TERMS if _contains_phrase(title, term))
    extreme = any(_contains_phrase(title, term) for term in EXTREME_SENIOR_TERMS)
    return sorted(set(signals)), extreme


def detect_experience(description: str | None) -> ExperienceSignal:
    text = normalize_text(description)
    unit = r"(?:years?|anos?)"
    context_after = (
        r"(?:of\s+)?(?:[a-z+#./-]+\s+){0,3}(?:experience|experiencia)"
        r"|in\s+(?:a\s+)?[a-z][a-z /+-]{0,45}?\s+role"
    )
    prefix = r"(?:minimum|minimo|at least|pelo menos|requires?|required|requirement|requisito)\s*[:\-]?\s*"
    matches: list[tuple[int, int | None, str, int, int]] = []
    patterns = [
        rf"(?:{prefix})?(\d+)\s*[-–]\s*(\d+)\s*{unit}\s*(?:{context_after})",
        rf"(?:{prefix})?(\d+)\s+to\s+(\d+)\s*{unit}\s*(?:{context_after})",
        rf"(?:{prefix})?(\d+)\s*\+\s*{unit}\s*(?:{context_after})",
        rf"{prefix}(\d+)\s*\+?\s*{unit}(?:\s*(?:{context_after}))?",
        rf"(?:{prefix})?(\d+)\s*{unit}\s*(?:{context_after})",
        rf"(?:experience|experiencia).{{0,30}}?(?:{prefix})?(\d+)\s*\+?\s*{unit}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            minimum = int(match.group(1))
            maximum = int(match.group(2)) if match.lastindex and match.lastindex >= 2 and match.group(2) else None
            if minimum > 20:
                continue
            matches.append((minimum, maximum, match.group(0), match.start(), match.end()))
    if not matches:
        return ExperienceSignal(None, None)
    ranges = [item for item in matches if item[1] is not None]
    matches = [
        item
        for item in matches
        if item[1] is not None or not any(ranged[3] <= item[3] and item[4] <= ranged[4] for ranged in ranges)
    ]
    years, maximum, phrase, _, _ = max(matches, key=lambda item: item[0])
    return ExperienceSignal(years, phrase, maximum)


def detect_location(job: Job) -> LocationSignal:
    title_location = normalize_text(" ".join([job.title, job.location or ""]))
    text = normalize_text(" ".join([job.title, job.location or "", job.description or ""]))
    remote = _contains_any(text, REMOTE_TERMS)
    exclusions = [term for term in EXCLUSION_TERMS if term in text]
    latam_exclusion = any(term in text for term in LATAM_EXCLUDING_BRAZIL)
    title_location_brazil = any(term in title_location for term in BRAZIL_TERMS)
    title_location_latam = any(term in title_location for term in LATAM_TERMS)
    title_location_americas = any(_contains_phrase(title_location, term) for term in AMERICAS_TERMS)
    title_location_worldwide = any(_contains_phrase(title_location, term) for term in WORLDWIDE_LOCATION_TERMS)
    title_location_foreign = any(term in f" {title_location} " for term in FOREIGN_TERMS)
    brazil = any(term in text for term in BRAZIL_TERMS)
    latam = any(term in text for term in LATAM_TERMS)
    latam_includes_brazil = any(term in text for term in LATAM_INCLUDE_BRAZIL_TERMS)
    americas = any(_contains_phrase(text, term) for term in AMERICAS_TERMS)
    worldwide = any(_contains_phrase(text, term) for term in WORLDWIDE_REMOTE_TERMS)
    foreign = any(term in f" {text} " for term in FOREIGN_TERMS)

    if latam_exclusion:
        return LocationSignal(remote, False, ["LATAM excluding Brazil"], ["LATAM excluding Brazil"], LocationCategory.BRAZIL_EXCLUDED)
    if exclusions:
        return LocationSignal(remote, False, sorted(set(exclusions)), exclusions, LocationCategory.FOREIGN_RESTRICTED)
    if title_location_foreign and not (
        title_location_brazil or title_location_latam or title_location_americas or title_location_worldwide or worldwide or latam_includes_brazil
    ):
        if remote:
            return LocationSignal(remote, False, ["Foreign restricted remote"], ["Foreign location with remote eligibility restricted"], LocationCategory.FOREIGN_RESTRICTED)
        return LocationSignal(remote, False, ["Foreign on-site location"], ["Foreign location: on-site outside Brazil"], LocationCategory.FOREIGN_ONSITE)
    if latam and (latam_includes_brazil or not foreign):
        return LocationSignal(remote, True, ["LATAM remote"], [], LocationCategory.LATAM_INCLUDING_BRAZIL)
    if brazil:
        return LocationSignal(remote, True, ["Brazil-compatible location"], [], LocationCategory.BRAZIL)
    if title_location_worldwide or worldwide:
        return LocationSignal(remote, True, ["Worldwide remote"], [], LocationCategory.GLOBAL)
    if americas and remote:
        return LocationSignal(remote, True, ["Americas remote"], [], LocationCategory.AMERICAS)
    if foreign:
        if remote:
            return LocationSignal(remote, False, ["Foreign restricted remote"], ["Foreign location with remote eligibility restricted"], LocationCategory.FOREIGN_RESTRICTED)
        return LocationSignal(remote, False, ["Foreign on-site location"], ["Foreign location: on-site outside Brazil"], LocationCategory.FOREIGN_ONSITE)
    if remote:
        return LocationSignal(remote, None, ["Remote geography unclear"], [], LocationCategory.REMOTE_UNSCOPED)
    return LocationSignal(remote, None, [], [], LocationCategory.UNKNOWN)


def freshness_days(job: Job, now: datetime) -> int | None:
    date = job.published_at or job.collected_at
    if date is None:
        return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return max((now.astimezone(timezone.utc) - date.astimezone(timezone.utc)).days, 0)
