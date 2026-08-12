from dataclasses import dataclass, field
from enum import Enum


class RelevanceBand(str, Enum):
    EXCELLENT = "EXCELLENT"
    STRONG = "STRONG"
    INTERESTING = "INTERESTING"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


@dataclass(frozen=True)
class RelevanceResult:
    score: int
    band: RelevanceBand
    profile: str
    version: str
    positive_reasons: list[str] = field(default_factory=list)
    negative_reasons: list[str] = field(default_factory=list)
    matched_roles: list[str] = field(default_factory=list)
    matched_technologies: list[str] = field(default_factory=list)
    matched_location_signals: list[str] = field(default_factory=list)
    matched_seniority_signals: list[str] = field(default_factory=list)
    components: dict[str, int] = field(default_factory=dict)

    def reasons_payload(self) -> dict:
        return {
            "positive": self.positive_reasons,
            "negative": self.negative_reasons,
            "matched_roles": self.matched_roles,
            "matched_technologies": self.matched_technologies,
            "matched_location_signals": self.matched_location_signals,
            "matched_seniority_signals": self.matched_seniority_signals,
        }


def band_for_score(score: int) -> RelevanceBand:
    if score >= 90:
        return RelevanceBand.EXCELLENT
    if score >= 75:
        return RelevanceBand.STRONG
    if score >= 60:
        return RelevanceBand.INTERESTING
    if score >= 40:
        return RelevanceBand.LOW
    return RelevanceBand.VERY_LOW

