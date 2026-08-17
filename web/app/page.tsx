import Link from "next/link";
import { ActivityPanel } from "@/components/home/activity-panel";
import { StatCard } from "@/components/home/stat-card";
import { JobList } from "@/components/jobs/job-list";
import { ErrorState } from "@/components/ui/error-state";
import { getJobs, getStats } from "@/lib/radar-api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const data = await loadHomeData();
  if (!data) {
    return <ErrorState message="Nao foi possivel carregar as oportunidades agora." />;
  }
  const [stats, jobs] = data;
  const bands = stats.jobs_by_relevance_band ?? {};

  return (
    <div className="space-y-5">
      <section>
        <h1 className="text-2xl font-semibold">Oportunidades para voce</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">Vagas coletadas e analisadas pelo Radar que mais combinam com o seu perfil.</p>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5" aria-label="Resumo">
        <StatCard label="Excelentes" value={bands.excellent ?? 0} hint="Score 90-100" tone="green" />
        <StatCard label="Fortes" value={bands.strong ?? 0} hint="Score 70-89" tone="blue" />
        <StatCard label="Interessantes" value={bands.interesting ?? 0} hint="Score 50-69" tone="amber" />
        <StatCard label="Vagas ativas" value={stats.jobs_active} hint={`${stats.jobs_total} no total`} />
        <StatCard label="Fontes ativas" value={stats.sources_enabled} hint={`${stats.company_sources_enabled} empresas`} />
      </section>

      <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
        <section>
          <div className="mb-2 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Mais relevantes para voce</h2>
            <Link className="text-sm font-medium text-[var(--blue)] hover:underline" href="/jobs">
              Ver todas as vagas
            </Link>
          </div>
          <JobList jobs={jobs.items} clearHref="/jobs" />
        </section>
        <ActivityPanel stats={stats} />
      </div>
    </div>
  );
}

async function loadHomeData() {
  try {
    return await Promise.all([getStats(), getJobs({ page: "1", page_size: "5", active: "true" })]);
  } catch {
    return null;
  }
}
