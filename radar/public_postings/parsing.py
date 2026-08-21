from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any


class JobPostingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.json_ld_blocks: list[str] = []
        self.canonical_urls: list[str] = []
        self.links: list[str] = []
        self._json_ld_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {key.casefold(): value for key, value in attrs if value is not None}
        if tag.casefold() == "script" and values.get("type", "").casefold() == "application/ld+json":
            self._json_ld_parts = []
        if tag.casefold() == "link" and "canonical" in values.get("rel", "").casefold().split():
            if values.get("href"):
                self.canonical_urls.append(values["href"])
        if tag.casefold() == "a" and values.get("href"):
            self.links.append(values["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "script" and self._json_ld_parts is not None:
            self.json_ld_blocks.append("".join(self._json_ld_parts))
            self._json_ld_parts = None

    def handle_data(self, data: str) -> None:
        if self._json_ld_parts is not None:
            self._json_ld_parts.append(data)


def parse_job_postings(html: str) -> tuple[list[dict[str, Any]], JobPostingHTMLParser, int]:
    parser = JobPostingHTMLParser()
    parser.feed(html)
    postings: list[dict[str, Any]] = []
    invalid_blocks = 0
    for block in parser.json_ld_blocks:
        try:
            payload = json.loads(block)
        except (TypeError, ValueError):
            invalid_blocks += 1
            continue
        postings.extend(_find_job_postings(payload))
    return postings, parser, invalid_blocks


def _find_job_postings(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            found.extend(_find_job_postings(item))
    elif isinstance(value, dict):
        types = value.get("@type")
        type_values = types if isinstance(types, list) else [types]
        if any(str(item).casefold() == "jobposting" for item in type_values):
            found.append(value)
        graph = value.get("@graph")
        if isinstance(graph, (dict, list)):
            found.extend(_find_job_postings(graph))
    return found
