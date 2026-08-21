from __future__ import annotations

from radar.public_postings.models import PublicPostingReport


def print_public_posting_report(report: PublicPostingReport) -> None:
    print("Public JobPosting read-only report")
    print(f"URLs discovered: {report.urls_discovered}")
    print(f"Pages read: {report.pages_read}")
    print(f"Valid JobPostings: {report.valid}")
    print(f"Active: {report.active}")
    print(f"Expired: {report.expired}")
    print(f"Invalid: {report.invalid}")
    print(f"Requests: {report.requests}")
    for posting in report.postings:
        location = _location(posting.location)
        company = posting.company or "Confidential / intermediary not treated as employer"
        print("---")
        print(f"ID: {posting.external_id or 'INVALID'}")
        print(f"Title: {posting.title or 'N/A'}")
        print(f"Company: {company}")
        print(f"Location: {location or 'N/A'}")
        print(f"Date posted: {posting.date_posted.isoformat() if posting.date_posted else 'N/A'}")
        print(f"Valid through: {posting.valid_through.isoformat() if posting.valid_through else 'N/A'}")
        print(f"Lifecycle: {posting.lifecycle.value}")
        print(f"Canonical: {posting.canonical_url}")
        print(f"Apply URL: {posting.apply_url or 'N/A'}")
        print(f"Description length: {len(posting.description or '')}")
        for issue in posting.metadata.get("issues", []):
            print(f"Issue: {issue}")
    for url in report.invalid_urls:
        print("---")
        print(f"Invalid page: {url}")


def _location(value) -> str | None:
    if isinstance(value, list):
        return "; ".join(filter(None, (_location(item) for item in value))) or None
    if not isinstance(value, dict):
        return str(value) if value else None
    address = value.get("address")
    if isinstance(address, dict):
        parts = [address.get("addressLocality"), address.get("addressRegion"), address.get("addressCountry")]
        return ", ".join(str(part) for part in parts if part) or None
    return None
