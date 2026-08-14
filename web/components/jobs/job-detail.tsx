import Link from "next/link";
import { ScoreBadge } from "@/components/jobs/score-badge";
import { TechnologyLabels } from "@/components/jobs/technology-labels";
import { formatEmploymentType, formatLongDate, formatRemoteType, formatSeniority } from "@/lib/formatters";
import type { JobDetail as JobDetailType } from "@/lib/types";

export function JobDetail({ job }: { job: JobDetailType }) {
  return (
    <div className="space-y-5">
      <nav className="text-sm text-[var(--muted)]" aria-label="Breadcrumb">
        <Link className="hover:text-slate-950" href="/jobs">
          Vagas
        </Link>
        <span className="px-2">/</span>
        <span>{job.title}</span>
      </nav>

      <div className="grid gap-5 lg:grid-cols-[1fr_320px] lg:items-start">
        <article className="min-w-0 space-y-5">
          <header className="panel p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <h1 className="text-2xl font-semibold">{job.title}</h1>
                <p className="mt-1 text-base font-medium">{job.company ?? "Empresa nao informada"}</p>
                <div className="mt-3 flex flex-wrap gap-x-2 gap-y-1 text-sm text-[var(--muted)]">
                  {job.location ? <span>{job.location}</span> : null}
                  <span>{formatRemoteType(job.remote_type)}</span>
                  <span>{formatEmploymentType(job.employment_type)}</span>
                  <span>{formatSeniority(job.seniority)}</span>
                </div>
                <div className="mt-3">
                  <TechnologyLabels technologies={job.technologies} limit={8} />
                </div>
              </div>
              <a className="inline-flex h-10 shrink-0 items-center justify-center rounded-md bg-[var(--blue)] px-4 text-sm font-semibold text-white" href={job.url} rel="noreferrer" target="_blank">
                Candidatar-se -&gt;
              </a>
            </div>
          </header>

          <section className="panel p-4">
            <h2 className="text-lg font-semibold">Sobre a vaga</h2>
            <div className="mt-4 space-y-3 text-sm leading-6">
              {descriptionParagraphs(job.description).map((paragraph, index) => (
                <p key={index}>{paragraph}</p>
              ))}
            </div>
          </section>

          {job.relevance_reasons ? (
            <section className="panel p-4">
              <h2 className="text-lg font-semibold">Sinais de relevancia</h2>
              <pre className="mt-3 overflow-x-auto rounded-md border border-[var(--border-muted)] bg-[var(--surface-subtle)] p-3 text-xs leading-5 text-slate-700">{JSON.stringify(job.relevance_reasons, null, 2)}</pre>
            </section>
          ) : null}
        </article>

        <aside className="space-y-4 lg:sticky lg:top-20">
          <section className="panel p-4">
            <h2 className="text-base font-semibold">Relevancia para voce</h2>
            <div className="mt-5">
              <ScoreBadge score={job.relevance_score} band={job.relevance_band} />
            </div>
          </section>
          <section className="panel p-4">
            <h2 className="text-base font-semibold">Informacoes</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <Info label="Empresa" value={job.company ?? "N/A"} />
              <Info label="Fonte" value={job.source} />
              <Info label="Publicada em" value={formatLongDate(job.published_at)} />
              <Info label="Coletada em" value={formatLongDate(job.first_seen_at)} />
              <Info label="Atualizada em" value={formatLongDate(job.last_seen_at)} />
              <Info label="Tipo" value={formatEmploymentType(job.employment_type)} />
              <Info label="Modalidade" value={formatRemoteType(job.remote_type)} />
              <Info label="Senioridade" value={formatSeniority(job.seniority)} />
            </dl>
          </section>
        </aside>
      </div>
    </div>
  );
}

function descriptionParagraphs(description: string | null): string[] {
  if (!description) return ["Descricao nao informada pela fonte."];
  return description
    .replace(/\r/g, "")
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[120px_1fr] gap-3">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="min-w-0 break-words font-medium">{value}</dd>
    </div>
  );
}
