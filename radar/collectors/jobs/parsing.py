from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import unescape
from html.parser import HTMLParser
import re
from typing import Any

from radar.models.enums import EmploymentType, RemoteType


class _HTMLTextParser(HTMLParser):
    block_tags = {"br", "p", "div", "li", "section", "article", "h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        raw = unescape("".join(self.parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
        return "\n".join(line for line in lines if line).strip()


def html_to_text(value: str | None) -> str | None:
    if not value:
        return None
    parser = _HTMLTextParser()
    parser.feed(value)
    return parser.text()


def parse_datetime(value: str | int | float | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_remote_type(value: str | None) -> RemoteType:
    if not value:
        return RemoteType.UNKNOWN
    normalized = _normalize(value)
    if normalized in {"remote", "remotely", "fully remote"}:
        return RemoteType.REMOTE
    if normalized in {"hybrid", "hibrido", "hibrida"}:
        return RemoteType.HYBRID
    if normalized in {"on site", "onsite", "on-site", "office", "in office"}:
        return RemoteType.ONSITE
    return RemoteType.UNKNOWN


def normalize_employment_type(value: str | None) -> EmploymentType:
    if not value:
        return EmploymentType.UNKNOWN
    normalized = _normalize(value).replace("_", " ")
    compact = normalized.replace("-", " ").replace(" ", "")
    if compact in {"intern", "internship", "estagio"}:
        return EmploymentType.INTERNSHIP
    if compact == "trainee":
        return EmploymentType.TRAINEE
    if compact in {"fulltime", "full"}:
        return EmploymentType.FULL_TIME
    if compact in {"parttime", "part"}:
        return EmploymentType.PART_TIME
    if compact in {"temporary", "temp"}:
        return EmploymentType.TEMPORARY
    if compact in {"contract", "contractor"}:
        return EmploymentType.CONTRACT
    return EmploymentType.UNKNOWN


def parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())

