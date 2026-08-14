import type { JobSearchParams } from "@/lib/types";

export const filterKeys = [
  "q",
  "source",
  "company",
  "remote",
  "employment_type",
  "seniority",
  "min_score",
  "max_score",
  "relevance_band",
  "active",
  "location",
  "technology",
] as const;

export type FilterKey = (typeof filterKeys)[number];

export function normalizeSearchParams(searchParams: Record<string, string | string[] | undefined>): JobSearchParams {
  const normalized: JobSearchParams = {};
  for (const key of [...filterKeys, "page", "page_size"] as const) {
    const value = searchParams[key];
    if (Array.isArray(value)) {
      normalized[key] = value[0];
    } else if (value) {
      normalized[key] = value;
    }
  }
  return normalized;
}

export function hrefWithParams(path: string, params: JobSearchParams, updates: JobSearchParams): string {
  const next = new URLSearchParams();
  for (const [key, value] of Object.entries({ ...params, ...updates })) {
    if (value !== undefined && value !== "") {
      next.set(key, value);
    }
  }
  const query = next.toString();
  return query ? `${path}?${query}` : path;
}

export function removeFilterHref(path: string, params: JobSearchParams, key: FilterKey): string {
  const next = { ...params, page: "1" };
  delete next[key];
  return hrefWithParams(path, next, {});
}

export function activeFilters(params: JobSearchParams): Array<{ key: FilterKey; label: string; value: string }> {
  return filterKeys.flatMap((key) => {
    const value = params[key];
    if (!value || (key === "active" && value === "true")) return [];
    return [{ key, label: filterLabel(key, value), value }];
  });
}

export function filterLabel(key: FilterKey, value: string): string {
  const labels: Record<FilterKey, string> = {
    q: "Busca",
    source: "Fonte",
    company: "Empresa",
    remote: "Remoto",
    employment_type: "Tipo",
    seniority: "Senioridade",
    min_score: "Score >=",
    max_score: "Score <=",
    relevance_band: "Faixa",
    active: "Ativa",
    location: "Local",
    technology: "Tecnologia",
  };
  if (key === "remote") return value === "true" ? "Remoto" : "Nao remoto";
  if (key === "min_score" || key === "max_score") return `${labels[key]} ${value}`;
  return `${labels[key]}: ${value}`;
}
