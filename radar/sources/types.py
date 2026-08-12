from enum import Enum


class ContentType(str, Enum):
    JOB = "job"
    DEAL = "deal"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    LEGACY = "legacy"
    EXPERIMENTAL = "experimental"

