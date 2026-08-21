import json
from pathlib import Path
from typing import Any

from radar.discovery.resolver import LocalDiscoveryResolver, ResolutionReport


def load_results(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("Discovery input must be a JSON array of objects")
    return payload


def resolve_file(path: Path) -> ResolutionReport:
    return LocalDiscoveryResolver().resolve_all(load_results(path))


def print_report(report: ResolutionReport) -> None:
    for candidate in report.unique_candidates:
        print("Candidate")
        print(f"Company: {candidate.company or 'N/A'}")
        print(f"Title: {candidate.observed_title or 'N/A'}")
        print(f"Location: {candidate.location or 'N/A'}")
        print(f"Discovered via: {candidate.discovered_via}")
        print(f"Canonical source: {candidate.probable_source}")
        print(f"Canonical URL: {candidate.canonical_url or 'N/A'}")
        print(f"External ID: {candidate.external_id or 'N/A'}")
        print(f"Status: {candidate.resolution_status.value}")
        print()

    print("Summary")
    print(f"Candidates found: {report.candidates_found}")
    print(f"Unique candidates: {len(report.unique_candidates)}")
    print(f"Duplicates removed: {report.duplicates_removed}")
    for source, count in sorted(report.sources.items()):
        print(f"Source {source}: {count}")
    for status, count in sorted(report.statuses.items()):
        print(f"Status {status}: {count}")
