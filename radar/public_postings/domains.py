from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PublicPostingDomain:
    name: str
    hostnames: frozenset[str]
    sitemap_url: str
    job_path_pattern: re.Pattern[str]
    intermediary_names: frozenset[str]
    apply_hostnames: frozenset[str]
    max_sitemaps: int = 12

    def external_id_from_path(self, path: str) -> str | None:
        match = self.job_path_pattern.fullmatch(path)
        return match.group("id") if match else None


PORTAL_DO_ESTAGIO = PublicPostingDomain(
    name="portal_do_estagio",
    hostnames=frozenset({"portaldoestagio.com.br", "www.portaldoestagio.com.br"}),
    sitemap_url="https://portaldoestagio.com.br/sitemap_index.xml",
    job_path_pattern=re.compile(r"/vaga/(?P<id>\d+)/?"),
    intermediary_names=frozenset({"portal do estágio", "portal do estagio"}),
    apply_hostnames=frozenset({"forms.gle", "docs.google.com"}),
)


DOMAIN_CONFIGS = {
    "portaldoestagio.com.br": PORTAL_DO_ESTAGIO,
}


def get_domain_config(domain: str) -> PublicPostingDomain:
    try:
        return DOMAIN_CONFIGS[domain.casefold().strip().rstrip(".")]
    except KeyError as exc:
        raise ValueError(f"Public JobPosting domain is not allowlisted: {domain}") from exc
