import Link from "next/link";
import { JobList } from "@/components/jobs/job-list";
import { JobShortcuts } from "@/components/jobs/job-shortcuts";
import { ErrorState } from "@/components/ui/error-state";
import { getCuratedJobs } from "@/lib/radar-api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const data = await loadHomeData();
  if (!data) {
    return <ErrorState message="Nao foi possivel carregar as oportunidades agora." />;
  }
  const jobs = data;
  const excellent = jobs.items.filter((job) => String(job.relevance_band).toLowerCase() === "excellent").length;
  const strong = jobs.items.filter((job) => String(job.relevance_band).toLowerCase() === "strong").length;

  return (
    <div className="space-y-5">
      <section className="panel hero-panel p-5 md:p-7">
        <p className="text-sm font-semibold uppercase tracking-wide text-[var(--blue)]">Radar</p>
        <h1 className="mt-2 text-3xl font-semibold">{jobs.total} boas oportunidades</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">{excellent} excelentes · {strong} fortes · selecionadas pela compatibilidade e localizacao</p>
        <div className="mt-5"><JobShortcuts active="for-me" /></div>
      </section>
      <section>
          <div className="mb-2 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Mais relevantes para voce</h2>
            <Link className="text-sm font-medium text-[var(--blue)] hover:underline" href="/jobs?view=for-me">
              Ver todas as vagas
            </Link>
          </div>
          <JobList jobs={jobs.items.slice(0, 6)} clearHref="/jobs?view=for-me" />
      </section>
    </div>
  );
}

async function loadHomeData() {
  try {
    return await getCuratedJobs({ view: "for-me", page: "1", page_size: "10000", active: "true" });
  } catch {
    return null;
  }
}
