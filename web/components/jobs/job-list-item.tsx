import Link from "next/link";
import { formatEmploymentType, formatRelativeDate } from "@/lib/formatters";
import { formatJobLocation } from "@/lib/job-location";
import type { JobListItem as JobListItemType } from "@/lib/types";
import { ScoreBadge } from "@/components/jobs/score-badge";
import { TechnologyLabels } from "@/components/jobs/technology-labels";
import { AttainabilityBadge } from "@/components/jobs/attainability-badge";

export function JobListItem({ job }: { job: JobListItemType }) {
  const location = formatJobLocation(job);
  const employment = formatEmploymentType(job.employment_type);
  const published = formatRelativeDate(job.published_at);
  return (
    <article className="grid gap-3 border-b border-[var(--border-muted)] p-4 transition-colors hover:bg-slate-50 md:grid-cols-[1fr_96px] md:items-start">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <Link className="text-base font-semibold text-[var(--blue)] hover:underline" href={`/jobs/${job.id}`}>
            {job.title}
          </Link>
          {job.company ? <span className="text-sm font-medium text-slate-800">{job.company}</span> : null}
        </div>
        <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1 text-sm text-[var(--muted)]">
          {location.map((part) => <span key={part}>{part}</span>)}
          {employment !== "Nao informado" ? <span>{employment}</span> : null}
        </div>
        <div className="mt-2">
          <TechnologyLabels technologies={job.technologies} />
        </div>
        {published !== "N/A" ? <p className="mt-2 text-xs text-[var(--muted)]">Publicada {published}</p> : null}
      </div>
      <div className="flex items-center justify-between md:block">
        <ScoreBadge score={job.relevance_score} band={job.relevance_band} compact />
        {job.attainability ? <div className="mt-2"><AttainabilityBadge level={job.attainability.level} /></div> : null}
        <Link className="rounded-md border border-[var(--border)] px-2 py-1 text-sm text-[var(--muted)] hover:bg-white md:hidden" href={`/jobs/${job.id}`}>
          Abrir
        </Link>
      </div>
    </article>
  );
}
