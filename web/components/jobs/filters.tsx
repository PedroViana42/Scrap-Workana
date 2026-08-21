import Link from "next/link";
import type { JobSearchParams, SourceItem } from "@/lib/types";
import { JobShortcuts } from "@/components/jobs/job-shortcuts";
import { activeFilters, hrefWithParams, removeFilterHref } from "@/lib/query-params";

export function JobFilters({ params, sources }: { params: JobSearchParams; sources: SourceItem[] }) {
  const filters = activeFilters(params);
  return (
    <section aria-label="Filtros de vagas" className="space-y-3">
      <form action="/jobs" className="space-y-3">
        <div className="flex gap-2">
          <label className="sr-only" htmlFor="q">
            Buscar vagas
          </label>
          <input
            className="h-10 min-w-0 flex-1 rounded-md border border-[var(--border)] bg-white px-3 text-sm"
            defaultValue={params.q}
            id="q"
            name="q"
            placeholder="Buscar por cargo, empresa ou tecnologia..."
          />
          <button className="h-10 rounded-md bg-[var(--blue)] px-4 text-sm font-semibold text-white" type="submit">
            Buscar
          </button>
        </div>
        <div className="flex items-center justify-between gap-3">
          <JobShortcuts active={params.view} />
        </div>
        <details className="[&>div]:hidden [&[open]>div]:block">
          <summary className="inline-flex h-9 cursor-pointer items-center rounded-md border border-[var(--border)] bg-white px-3 text-sm font-medium">+ Filtros</summary>
          <div className="mt-3">
            <FilterControls params={params} sources={sources} />
          </div>
        </details>
        {params.view ? <input type="hidden" name="view" value={params.view} /> : null}
        <input type="hidden" name="page" value="1" />
      </form>
      {filters.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          {filters.map((filter) => (
            <Link className="rounded-md border border-blue-200 bg-[var(--blue-subtle)] px-2.5 py-1 text-sm font-medium text-[var(--blue)]" href={removeFilterHref("/jobs", params, filter.key)} key={filter.key}>
              {filter.label} x
            </Link>
          ))}
          <Link className="text-sm text-[var(--muted)] hover:text-slate-950" href="/jobs">
            Limpar filtros
          </Link>
        </div>
      ) : null}
    </section>
  );
}

function FilterControls({ params, sources }: { params: JobSearchParams; sources: SourceItem[] }) {
  return (
    <div className="grid grid-cols-2 gap-2 md:flex md:flex-wrap">
      <Select
        name="attainability"
        label="Nivel da oportunidade"
        value={params.attainability}
        options={[["", "Todas"], ["HIGH", "Inicio de carreira"], ["MEDIUM", "Intermediario"], ["LOW", "Avancado"]]}
      />
      <Select name="remote" label="Remote" value={params.remote} options={[["", "Remote"], ["true", "Remoto"], ["false", "Nao remoto"]]} />
      <Select
        name="seniority"
        label="Senioridade"
        value={params.seniority}
        options={[
          ["", "Senioridade"],
          ["intern", "Estagio"],
          ["junior", "Junior"],
          ["mid", "Pleno"],
          ["senior", "Senior"],
          ["lead", "Lead"],
        ]}
      />
      <Select
        name="employment_type"
        label="Tipo"
        value={params.employment_type}
        options={[
          ["", "Tipo"],
          ["full_time", "Tempo integral"],
          ["part_time", "Meio periodo"],
          ["internship", "Estagio"],
          ["contract", "Contrato"],
          ["temporary", "Temporario"],
        ]}
      />
      <input className="h-9 rounded-md border border-[var(--border)] bg-white px-3 text-sm" defaultValue={params.technology} name="technology" placeholder="Tecnologia" />
      <Select name="source" label="Fonte" value={params.source} options={[["", "Fonte"], ...sources.map((source) => [source.name, source.display_name] as [string, string])]} />
      <input className="h-9 rounded-md border border-[var(--border)] bg-white px-3 text-sm" defaultValue={params.location} name="location" placeholder="Localizacao" />
      <Select
        name="min_score"
        label="Score"
        value={params.min_score}
        options={[
          ["", "Score"],
          ["90", "Score >= 90"],
          ["70", "Score >= 70"],
          ["50", "Score >= 50"],
        ]}
      />
    </div>
  );
}

function Select({ name, label, value, options }: { name: string; label: string; value?: string; options: Array<[string, string]> }) {
  return (
    <div>
      <label className="sr-only" htmlFor={name}>
        {label}
      </label>
      <select className="not-sr-only h-9 w-full rounded-md border border-[var(--border)] bg-white px-3 text-sm md:w-auto" defaultValue={value ?? ""} id={name} name={name}>
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </div>
  );
}

export function pageHref(params: JobSearchParams, page: number) {
  return hrefWithParams("/jobs", params, { page: String(page) });
}
