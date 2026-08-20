import Link from "next/link";
import { ScoreBadge } from "@/components/jobs/score-badge";
import { TechnologyLabels } from "@/components/jobs/technology-labels";
import { JobDescription } from "@/components/jobs/job-description";
import { RelevanceExplanation } from "@/components/jobs/relevance-explanation";
import { AttainabilityExplanation } from "@/components/jobs/attainability-explanation";
import { formatEmploymentType, formatLongDate, formatRemoteType, formatSeniority } from "@/lib/formatters";
import { formatJobLocation } from "@/lib/job-location";
import type { JobDetail as JobDetailType } from "@/lib/types";

export function JobDetail({ job }: { job: JobDetailType }) {
  const location = formatJobLocation(job);
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
                {job.company ? <p className="mt-1 text-base font-medium">{job.company}</p> : null}
                <div className="mt-3 flex flex-wrap gap-x-2 gap-y-1 text-sm text-[var(--muted)]">
                  {location.map((part) => <span key={part}>{part}</span>)}
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

          {job.relevance_reasons?.positive?.length || job.relevance_reasons?.negative?.length ? (
            <section className="panel p-4"><RelevanceExplanation reasons={job.relevance_reasons} /></section>
          ) : null}

          {job.attainability ? <section className="panel p-4"><AttainabilityExplanation attainability={job.attainability} /></section> : null}

          <section className="panel p-4">
            <h2 className="text-lg font-semibold">Sobre a vaga</h2>
            <div className="mt-4"><JobDescription description={job.description} /></div>
          </section>
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
              {job.company ? <Info label="Empresa" value={job.company} /> : null}
              <Info label="Fonte" value={job.source} />
              {job.published_at ? <Info label="Publicada em" value={formatLongDate(job.published_at)} /> : null}
              <Info label="Coletada em" value={formatLongDate(job.first_seen_at)} />
              <Info label="Atualizada em" value={formatLongDate(job.last_seen_at)} />
              {formatEmploymentType(job.employment_type) !== "Nao informado" ? <Info label="Tipo" value={formatEmploymentType(job.employment_type)} /> : null}
              {formatRemoteType(job.remote_type) !== "Nao informado" ? <Info label="Modalidade" value={formatRemoteType(job.remote_type)} /> : null}
              {formatSeniority(job.seniority) !== "Nao informado" ? <Info label="Senioridade" value={formatSeniority(job.seniority)} /> : null}
            </dl>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[120px_1fr] gap-3">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="min-w-0 break-words font-medium">{value}</dd>
    </div>
  );
}
