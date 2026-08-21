from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

from radar.collectors.jobs.parsing import html_to_text, parse_datetime
from radar.discovery.resolver import normalize_url
from radar.http import HTTPClient, HTTPClientError
from radar.public_postings.domains import PublicPostingDomain, get_domain_config
from radar.public_postings.models import PostingLifecycle, PublicJobPosting, PublicPostingReport
from radar.public_postings.parsing import parse_job_postings


class PublicJobPostingAdapter:
    """Read allowlisted sitemaps and JobPosting JSON-LD without persistence."""

    def __init__(self, domain: str, *, client: HTTPClient | None = None) -> None:
        self.config = get_domain_config(domain)
        self.client = client or HTTPClient(max_retries=1)
        self.requests = 0

    def run(self, *, limit: int = 20, now: datetime | None = None) -> PublicPostingReport:
        if limit < 1 or limit > 20:
            raise ValueError("limit must be between 1 and 20")
        urls = self.discover_urls(limit=limit)
        postings: list[PublicJobPosting] = []
        invalid_urls: list[str] = []
        for url in urls:
            try:
                html = self._get_text(url)
                postings.append(self.parse_page(url, html, now=now))
            except (HTTPClientError, ValueError):
                invalid_urls.append(url)
        return PublicPostingReport(
            urls_discovered=len(urls),
            pages_read=len(urls),
            postings=tuple(postings),
            invalid_urls=tuple(invalid_urls),
            requests=self.requests,
        )

    def discover_urls(self, *, limit: int) -> list[str]:
        pending = [self.config.sitemap_url]
        visited: set[str] = set()
        jobs: list[str] = []
        while pending and len(visited) < self.config.max_sitemaps and len(jobs) < limit:
            sitemap_url = pending.pop(0)
            self._validate_url(sitemap_url)
            if sitemap_url in visited:
                continue
            visited.add(sitemap_url)
            root = ElementTree.fromstring(self._get_text(sitemap_url))
            namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            if root.tag == f"{namespace}sitemapindex" or root.tag.endswith("sitemapindex"):
                for element in root.findall(f".//{namespace}loc"):
                    child = (element.text or "").strip()
                    if child and self._is_allowed_url(child):
                        pending.append(child)
                continue
            entries: list[tuple[str, str]] = []
            for url_element in root.findall(f".//{namespace}url"):
                location = url_element.find(f"{namespace}loc")
                modified = url_element.find(f"{namespace}lastmod")
                candidate = (location.text or "").strip() if location is not None else ""
                last_modified = (modified.text or "").strip() if modified is not None else ""
                entries.append((last_modified, candidate))
            # WordPress sitemaps are not required to be newest-first. Prefer
            # recent postings when a caller deliberately imposes a low limit.
            entries.sort(key=lambda item: item[0], reverse=True)
            for _, candidate in entries:
                normalized = self._normalized_job_url(candidate)
                if normalized and normalized not in jobs:
                    jobs.append(normalized)
                    if len(jobs) >= limit:
                        break
        return jobs

    def parse_page(self, discovered_url: str, html: str, *, now: datetime | None = None) -> PublicJobPosting:
        self._validate_url(discovered_url, require_job=True)
        payloads, parsed_html, invalid_blocks = parse_job_postings(html)
        if not payloads:
            raise ValueError("Page does not contain a valid JobPosting JSON-LD object")
        payload = payloads[0]
        canonical = self._select_canonical(discovered_url, parsed_html.canonical_urls)
        url_id = self._external_id(canonical)
        schema_id = _identifier_value(payload.get("identifier"))
        issues: list[str] = []
        if schema_id and url_id and schema_id != url_id:
            issues.append(f"external_id_mismatch:url={url_id},identifier={schema_id}")

        valid_through = parse_datetime(payload.get("validThrough"))
        reference = now or datetime.now(timezone.utc)
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        lifecycle = PostingLifecycle.EXPIRED if valid_through and valid_through < reference else PostingLifecycle.ACTIVE
        if issues:
            lifecycle = PostingLifecycle.INVALID

        organization = payload.get("hiringOrganization")
        organization = organization if isinstance(organization, dict) else None
        organization_name = _text(organization.get("name")) if organization else None
        company = None if _normalized_name(organization_name) in self.config.intermediary_names else organization_name
        apply_url = self._extract_apply_url(parsed_html.links)
        metadata = {
            "identifier_from_schema": schema_id,
            "identifier_from_url": url_id,
            "issues": issues,
            "invalid_json_ld_blocks": invalid_blocks,
        }
        if organization and company is None:
            metadata["intermediary_hiring_organization"] = organization

        return PublicJobPosting(
            source=self.config.name,
            external_id=url_id if not issues else None,
            canonical_url=canonical,
            title=html_to_text(_text(payload.get("title"))),
            description=html_to_text(_text(payload.get("description"))),
            date_posted=parse_datetime(payload.get("datePosted")),
            valid_through=valid_through,
            employment_type=_string_or_list(payload.get("employmentType")),
            hiring_organization=organization,
            company=company,
            location=payload.get("jobLocation"),
            applicant_location_requirements=payload.get("applicantLocationRequirements"),
            job_location_type=_text(payload.get("jobLocationType")),
            base_salary=payload.get("baseSalary"),
            direct_apply=payload.get("directApply") if isinstance(payload.get("directApply"), bool) else None,
            apply_url=apply_url,
            lifecycle=lifecycle,
            raw_json_ld=payload,
            metadata=metadata,
        )

    def _select_canonical(self, discovered_url: str, candidates: list[str]) -> str:
        for candidate in candidates:
            absolute = urljoin(discovered_url, candidate)
            normalized = self._normalized_job_url(absolute)
            if normalized:
                return normalized
        normalized = self._normalized_job_url(discovered_url)
        if not normalized:  # protected by validation, retained defensively
            raise ValueError("Invalid discovered job URL")
        return normalized

    def _extract_apply_url(self, links: list[str]) -> str | None:
        for link in links:
            try:
                normalized = normalize_url(link)
            except ValueError:
                continue
            if (urlsplit(normalized).hostname or "").casefold() in self.config.apply_hostnames:
                return normalized
        return None

    def _normalized_job_url(self, url: str) -> str | None:
        try:
            normalized = normalize_url(url)
            self._validate_url(normalized, require_job=True)
            return normalized
        except ValueError:
            return None

    def _external_id(self, url: str) -> str | None:
        return self.config.external_id_from_path(urlsplit(url).path)

    def _is_allowed_url(self, url: str) -> bool:
        try:
            self._validate_url(url)
            return True
        except ValueError:
            return False

    def _validate_url(self, url: str, *, require_job: bool = False) -> None:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or (parsed.hostname or "").casefold() not in self.config.hostnames:
            raise ValueError("URL is outside the allowlisted HTTPS domain")
        if parsed.username or parsed.password or parsed.port not in {None, 443}:
            raise ValueError("URL contains unsupported authority components")
        if require_job and self.config.external_id_from_path(parsed.path) is None:
            raise ValueError("URL is not an allowlisted job path")

    def _get_text(self, url: str) -> str:
        current = url
        for _ in range(4):
            self._validate_url(current)
            self.requests += 1
            response = self.client.get(
                current,
                headers={"Accept": "text/html, application/xml;q=0.9"},
                allow_redirects=False,
            )
            if response.status_code not in {301, 302, 303, 307, 308}:
                return response.text
            location = response.headers.get("Location")
            if not location:
                raise ValueError("Redirect response does not include Location")
            current = urljoin(current, location)
        raise ValueError("Too many redirects")


def _identifier_value(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("value") or value.get("name")
    text = _text(value)
    return text if text and text.isdigit() else None


def _text(value: Any) -> str | None:
    if not isinstance(value, (str, int, float)):
        return None
    result = str(value).strip()
    return result or None


def _normalized_name(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _string_or_list(value: Any) -> str | list[str] | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return None
