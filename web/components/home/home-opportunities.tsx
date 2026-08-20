import Link from "next/link";
import { JobList } from "@/components/jobs/job-list";
import type { JobListItem } from "@/lib/types";

export function HomeOpportunities({ grounded, stretch }: { grounded: JobListItem[]; stretch: JobListItem[] }) {
  return (
    <div className="space-y-7">
      <section>
        <div className="mb-2 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">🎯 Mais pe no chao</h2>
            <p className="text-sm text-[var(--muted)]">Boa compatibilidade e perfil de entrada.</p>
          </div>
          <Link className="text-sm font-medium text-[var(--blue)] hover:underline" href="/jobs?view=for-me&attainability=HIGH">Ver mais vagas</Link>
        </div>
        {grounded.length ? <JobList jobs={grounded.slice(0, 6)} clearHref="/jobs?view=for-me&attainability=HIGH" /> : (
          <div className="panel p-5 text-sm text-[var(--muted)]">Nenhuma oportunidade bem alinhada apareceu agora. Veja as vagas que ainda podem valer uma tentativa.</div>
        )}
      </section>
      {stretch.length ? (
        <section>
          <div className="mb-2 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">🚀 Vale tentar</h2>
              <p className="text-sm text-[var(--muted)]">Oportunidades stretch que ainda parecem plausiveis.</p>
            </div>
            <Link className="text-sm font-medium text-[var(--blue)] hover:underline" href="/jobs?view=for-me&attainability=MEDIUM">Ver mais vagas</Link>
          </div>
          <JobList jobs={stretch.slice(0, 4)} clearHref="/jobs?view=for-me&attainability=MEDIUM" />
        </section>
      ) : null}
    </div>
  );
}
