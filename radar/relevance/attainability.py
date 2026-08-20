from __future__ import annotations

from dataclasses import dataclass
import re

from radar.models.job import Job
from radar.relevance.models import AttainabilityLevel, AttainabilityResult
from radar.relevance.signals import normalize_text


EARLY_TITLE_TERMS = [
    "intern", "internship", "estagio", "estagiario", "trainee", "apprentice", "jovem aprendiz",
    "graduate", "new grad", "junior", "jr", "entry level", "early career", "associate",
]
MID_TITLE_TERMS = ["mid level", "midlevel", "pleno"]
LEVEL_TWO_TERMS = ["engineer ii", "developer ii", "level ii", "level 2"]
LEVEL_THREE_TERMS = ["engineer iii", "developer iii", "level iii", "level 3", "senior ii"]
SENIOR_TITLE_TERMS = ["senior", "sr", "staff", "principal", "lead", "architect", "manager"]

ENTRY_DESCRIPTION_SIGNALS = {
    "Accepts recent graduates": ["recent graduates welcome", "new graduates welcome", "recem formados", "recem-formados"],
    "No prior professional experience required": [
        "no prior professional experience required", "previous experience is not required",
        "no previous experience required", "nao exige experiencia profissional", "experiencia anterior nao e necessaria",
    ],
    "Students are welcome": ["students are welcome", "estudantes sao bem vindos", "estudantes sao bem-vindos"],
    "Currently pursuing a degree": ["currently pursuing a degree", "cursando graduacao", "graduacao em andamento"],
    "Training provided": ["training provided", "treinamento fornecido", "treinamento oferecido"],
    "Mentorship provided": ["mentorship provided", "mentorship available", "mentoring provided", "mentoria oferecida", "mentoria disponivel"],
}

RESPONSIBILITY_SIGNALS = {
    "Independent production ownership": [
        "operate independently", "work independently", "independent ownership", "own production services",
        "production ownership", "services independently", "end to end ownership", "full ownership",
        "take ownership for its behavior in production", "autonomia total", "atuar de forma independente",
    ],
    "Architecture ownership": ["own architecture", "architecture ownership", "define architecture", "definir arquitetura"],
    "Technical leadership responsibility": [
        "technical leadership", "cross team technical leadership", "lead projects", "lead technical projects",
        "lideranca tecnica", "liderar projetos",
    ],
    "Mentors other engineers": ["mentor engineers", "mentor other engineers", "mentor fellow", "coach engineers", "mentorar engenheiros"],
    "On-call ownership expected": [
        "on call rotation", "on-call rotation", "lead incidents", "incident response", "security incident response",
        "resposta a incidentes", "plantao de incidentes",
    ],
    "Large-scale critical systems responsibility": [
        "design large scale systems", "distributed systems at scale", "high availability at scale",
        "mission critical systems", "mission-critical systems", "sistemas de missao critica",
    ],
    "Deep professional expertise expected": ["proven track record", "deep expertise", "strong expertise", "extensive experience", "expert level", "ideal candidate is an expert"],
}

PREFERRED_TERMS = ["preferred", "nice to have", "nice-to-have", "bonus", "desirable", "would be a plus", "desejavel", "diferencial"]
REQUIRED_TERMS = ["required", "must have", "minimum", "at least", "requires", "requirement", "requisito", "obrigatorio", "necessario", "pelo menos", "minimo"]


@dataclass(frozen=True)
class ExperienceRequirement:
    minimum: int
    maximum: int | None
    preferred: bool
    phrase: str


def classify_attainability(job: Job) -> AttainabilityResult:
    title = normalize_text(job.title).replace("-", " ")
    description = normalize_text(job.description).replace("-", " ")
    positive: list[str] = []
    warnings: list[str] = []
    negative: list[str] = []

    early_title = _matched(title, EARLY_TITLE_TERMS)
    mid_title = _matched(title, MID_TITLE_TERMS)
    level_two = _matched(title, LEVEL_TWO_TERMS)
    level_three = _matched(title, LEVEL_THREE_TERMS)
    senior_title = _matched(title, SENIOR_TITLE_TERMS)

    if early_title:
        positive.append(_early_title_reason(early_title))
    if mid_title:
        warnings.append("Mid-level title")
    if level_two:
        warnings.append("Engineer II title")
    if level_three:
        negative.append("Engineer III or equivalent title")
    if senior_title:
        negative.append("Senior-level title")

    for reason, phrases in ENTRY_DESCRIPTION_SIGNALS.items():
        if any(phrase in description for phrase in phrases):
            positive.append(reason)

    requirements = detect_experience_requirements(job.description)
    required = [item for item in requirements if not item.preferred]
    preferred = [item for item in requirements if item.preferred]
    highest_required = max(required, key=lambda item: item.minimum, default=None)
    highest_preferred = max(preferred, key=lambda item: item.minimum, default=None)

    if highest_required:
        if highest_required.minimum <= 1:
            positive.append(_experience_reason(highest_required))
        elif highest_required.minimum == 2:
            warnings.append(_experience_reason(highest_required))
        elif highest_required.minimum == 3:
            warnings.append(_experience_reason(highest_required))
        else:
            negative.append(_experience_reason(highest_required))
    if highest_preferred:
        reason = f"{_experience_reason(highest_preferred)} preferred"
        if highest_preferred.minimum <= 2:
            positive.append(reason)
        else:
            warnings.append(reason)

    responsibility_reasons = [reason for reason, phrases in RESPONSIBILITY_SIGNALS.items() if any(phrase in description for phrase in phrases)]
    warnings.extend(responsibility_reasons)

    strong_title = bool(senior_title or level_three)
    high_experience = highest_required is not None and highest_required.minimum >= 4
    three_plus_with_context = (
        highest_required is not None
        and highest_required.minimum >= 3
        and bool(mid_title or level_two or responsibility_reasons)
    )
    responsibility_cluster = len(responsibility_reasons) >= 3

    if strong_title or high_experience or three_plus_with_context or responsibility_cluster:
        negative.extend(reason for reason in responsibility_reasons if reason not in negative)
        warnings = [reason for reason in warnings if reason not in responsibility_reasons]
        level = AttainabilityLevel.LOW
    elif mid_title or level_two or (highest_required is not None and highest_required.minimum >= 2) or responsibility_reasons:
        level = AttainabilityLevel.MEDIUM
    elif early_title or positive:
        level = AttainabilityLevel.HIGH
    else:
        level = AttainabilityLevel.MEDIUM
        warnings.append("Career level is not explicit")

    return AttainabilityResult(
        level=level,
        positive=sorted(set(positive)),
        warnings=sorted(set(warnings)),
        negative=sorted(set(negative)),
    )


def detect_experience_requirements(description: str | None) -> list[ExperienceRequirement]:
    text = normalize_text((description or "").replace("–", "-").replace("—", "-"))
    if not text:
        return []
    pattern = re.compile(
        r"(?<!\d)(\d{1,2})\s*(?:(?:-|to|a)\s*(\d{1,2})|\+)?\s*(?:years?|anos?)"
        r"(?:"
        r"(?:\s+(?:of|de))?\s+(?:[a-z+#./-]+\s+){0,4}(?:experience|experiencia)"
        r"|\s+in\s+(?:a\s+)?[a-z][a-z /+.-]{0,45}?\s+role"
        r")"
        r"|(?:experience|experiencia)[^.;:\n]{0,35}?(\d{1,2})\s*\+?\s*(?:years?|anos?)"
        r"|(?:minimum|minimo|at least|pelo menos|requires?|required|requisito)\s*[:]?\s*"
        r"(\d{1,2})\s*(?:(?:-|to|a)\s*(\d{1,2})|\+)?\s*(?:years?|anos?)"
    )
    results: list[ExperienceRequirement] = []
    for match in pattern.finditer(text):
        minimum = int(match.group(1) or match.group(3) or match.group(4))
        if minimum > 20:
            continue
        maximum_value = match.group(2) or match.group(5)
        maximum = int(maximum_value) if maximum_value else None
        context = _requirement_context(text, match.start(), match.end())
        preferred = any(term in context for term in PREFERRED_TERMS)
        explicitly_required = any(term in context for term in REQUIRED_TERMS)
        if preferred and explicitly_required:
            preferred = _nearest_marker_distance(context, PREFERRED_TERMS) < _nearest_marker_distance(context, REQUIRED_TERMS)
        phrase = match.group(0).strip()
        results.append(ExperienceRequirement(minimum, maximum, preferred, phrase))
    return _deduplicate_requirements(results)


def _matched(text: str, terms: list[str]) -> str | None:
    for term in terms:
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text):
            return term
    return None


def _early_title_reason(term: str) -> str:
    if term in {"graduate", "new grad"}:
        return "Graduate role"
    if term in {"intern", "internship", "estagio", "estagiario"}:
        return "Internship role"
    return "Explicit junior role"


def _experience_reason(requirement: ExperienceRequirement) -> str:
    if requirement.maximum is not None:
        return f"{requirement.minimum}-{requirement.maximum} years experience"
    return f"{requirement.minimum}+ years experience"


def _nearest_marker_distance(context: str, terms: list[str]) -> int:
    center = len(context) // 2
    positions = [context.find(term) for term in terms if term in context]
    return min((abs(position - center) for position in positions), default=len(context))


def _requirement_context(text: str, start: int, end: int) -> str:
    left = max(text.rfind(separator, 0, start) for separator in [".", ";", "\n"])
    right_positions = [position for separator in [".", ";", "\n"] if (position := text.find(separator, end)) >= 0]
    right = min(right_positions, default=len(text))
    return text[left + 1:right]


def _deduplicate_requirements(requirements: list[ExperienceRequirement]) -> list[ExperienceRequirement]:
    unique: dict[tuple[int, int | None, bool], ExperienceRequirement] = {}
    for requirement in requirements:
        unique[(requirement.minimum, requirement.maximum, requirement.preferred)] = requirement
    return list(unique.values())
