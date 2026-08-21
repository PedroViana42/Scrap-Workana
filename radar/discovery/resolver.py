from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from radar.discovery.models import DiscoveryCandidate, ResolutionStatus


SUPPORTED_SOURCES = {"greenhouse", "lever", "ashby", "workable", "smartrecruiters"}
PARTNERSHIP_SOURCES = {"gupy", "pandape"}
DISCOVERY_SOURCES = {"linkedin", "aggregator"}

_TRACKING_KEYS = {
    "fbclid", "gclid", "gh_src", "jobboardsource", "ref", "referral", "source", "trk",
    "tracking", "trackingid", "mc_cid", "mc_eid",
}
_TRACKING_PREFIXES = ("utm_",)


@dataclass(frozen=True)
class ResolutionReport:
    candidates_found: int
    unique_candidates: tuple[DiscoveryCandidate, ...]

    @property
    def duplicates_removed(self) -> int:
        return self.candidates_found - len(self.unique_candidates)

    @property
    def sources(self) -> Counter[str]:
        return Counter(candidate.probable_source for candidate in self.unique_candidates)

    @property
    def statuses(self) -> Counter[str]:
        return Counter(candidate.resolution_status.value for candidate in self.unique_candidates)


class LocalDiscoveryResolver:
    """Classify supplied public results without fetching URLs or writing data."""

    def resolve(self, raw: Mapping[str, Any]) -> DiscoveryCandidate:
        discovered_url = _required_text(raw, "discovered_url")
        canonical_input = _text(raw.get("resolved_url")) or discovered_url
        canonical_url = _try_normalize_url(canonical_input)
        discovered_normalized = _try_normalize_url(discovered_url)
        discovered_via = _text(raw.get("discovered_via")) or identify_source(discovered_normalized)
        source = identify_source(canonical_url)
        external_id = extract_external_id(source, canonical_url)
        raw_metadata = raw.get("metadata")
        if raw_metadata is not None and not isinstance(raw_metadata, Mapping):
            raise ValueError("Discovery metadata must be an object")
        return DiscoveryCandidate(
            discovered_url=discovered_url,
            canonical_url=canonical_url,
            observed_title=_text(raw.get("observed_title")),
            company=_text(raw.get("company")),
            location=_text(raw.get("location")),
            discovered_via=discovered_via,
            probable_source=source,
            external_id=external_id,
            resolution_status=resolution_status(source),
            metadata=dict(raw_metadata or {}),
        )

    def resolve_all(self, rows: Iterable[Mapping[str, Any]]) -> ResolutionReport:
        candidates = [self.resolve(row) for row in rows]
        unique: dict[tuple[str, ...], DiscoveryCandidate] = {}
        for candidate in candidates:
            unique.setdefault(candidate.deduplication_key, candidate)
        return ResolutionReport(len(candidates), tuple(unique.values()))


def normalize_url(value: str) -> str:
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"Invalid public HTTP(S) URL: {value!r}")
    hostname = parsed.hostname.casefold().rstrip(".")
    port = parsed.port
    netloc = hostname
    if port and not ((parsed.scheme.casefold() == "http" and port == 80) or (parsed.scheme.casefold() == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not _is_tracking_key(key)
    ]
    return urlunsplit((parsed.scheme.casefold(), netloc, path, urlencode(sorted(query)), ""))


def identify_source(url: str | None) -> str:
    if not url:
        return "unknown"
    host = (urlsplit(url).hostname or "").casefold()
    path = urlsplit(url).path.casefold()
    if "greenhouse.io" in host:
        return "greenhouse"
    if host == "jobs.lever.co" or host.endswith(".jobs.lever.co"):
        return "lever"
    if host == "jobs.ashbyhq.com":
        return "ashby"
    if "workable.com" in host:
        return "workable"
    if "smartrecruiters.com" in host:
        return "smartrecruiters"
    if host.endswith(".gupy.io") or host == "gupy.io":
        return "gupy"
    if "zohorecruit" in host or "zohopublic.com" in host or "careers-page.com" in host:
        return "zoho_recruit"
    if "solides.com" in host:
        return "solides"
    if "pandape" in host or ("infojobs.com" in host and "/detail" in path):
        return "pandape"
    if "rhgestor" in host:
        return "rh_gestor"
    if "portaldoestagio" in host:
        return "portal_do_estagio"
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        return "linkedin"
    if any(name in host for name in ("indeed.", "glassdoor.", "jooble.")):
        return "aggregator"
    if host in {"bit.ly", "lnkd.in", "t.co", "tinyurl.com"}:
        return "unknown"
    return "company_site" if host else "unknown"


def resolution_status(source: str) -> ResolutionStatus:
    if source in SUPPORTED_SOURCES:
        return ResolutionStatus.RESOLVED_SUPPORTED
    if source in PARTNERSHIP_SOURCES:
        return ResolutionStatus.PARTNERSHIP_REQUIRED
    if source in DISCOVERY_SOURCES:
        return ResolutionStatus.DISCOVERY_ONLY
    if source in {"zoho_recruit", "solides", "rh_gestor", "portal_do_estagio", "company_site"}:
        return ResolutionStatus.RESOLVED_UNSUPPORTED
    return ResolutionStatus.UNKNOWN


def extract_external_id(source: str, url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlsplit(url)
    segments = [segment for segment in parsed.path.split("/") if segment]
    patterns: dict[str, tuple[re.Pattern[str], ...]] = {
        "greenhouse": (re.compile(r"/jobs/(\d+)(?:/|$)", re.I),),
        "gupy": (re.compile(r"/jobs/(\d+)(?:/|$)", re.I),),
        "solides": (re.compile(r"/vaga/(\d+)(?:/|$)", re.I),),
        "pandape": (re.compile(r"/detail/(\d+)(?:/|$)", re.I),),
        "portal_do_estagio": (re.compile(r"/vaga/(\d+)(?:/|$)", re.I),),
        "smartrecruiters": (
            re.compile(r"/postings/([^/]+)(?:/|$)", re.I),
            re.compile(r"/[^/]+/([0-9a-f-]{20,})(?:-[^/]*)?$", re.I),
        ),
        "workable": (re.compile(r"/(?:j|view)/([A-Z0-9]+)(?:/|$)", re.I),),
    }
    for pattern in patterns.get(source, ()):
        match = pattern.search(parsed.path)
        if match:
            return match.group(1)
    if source in {"lever", "ashby"} and len(segments) >= 2:
        candidate = segments[-1]
        if re.fullmatch(r"[0-9a-z-]{8,}", candidate, re.I):
            return candidate
    return None


def _is_tracking_key(key: str) -> bool:
    normalized = key.casefold()
    return normalized in _TRACKING_KEYS or normalized.startswith(_TRACKING_PREFIXES)


def _try_normalize_url(value: str) -> str | None:
    try:
        return normalize_url(value)
    except (ValueError, UnicodeError):
        return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(raw: Mapping[str, Any], key: str) -> str:
    value = _text(raw.get(key))
    if not value:
        raise ValueError(f"Missing required field: {key}")
    return value
