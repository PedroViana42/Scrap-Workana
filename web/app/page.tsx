import { JobShortcuts } from "@/components/jobs/job-shortcuts";
import { HomeOpportunities } from "@/components/home/home-opportunities";
import { ErrorState } from "@/components/ui/error-state";
import { getCuratedJobs } from "@/lib/radar-api";
import { homeGroupForJob } from "@/lib/job-location";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const data = await loadHomeData();
  if (!data) {
    return <ErrorState message="Nao foi possivel carregar as oportunidades agora." />;
  }
  const jobs = data;
  const grounded = jobs.items.filter((job) => homeGroupForJob(job) === "grounded");
  const stretch = jobs.items.filter((job) => homeGroupForJob(job) === "stretch");

  return (
    <div className="space-y-5">
      <section className="panel hero-panel p-5 md:p-7">
        <p className="text-sm font-semibold uppercase tracking-wide text-[var(--blue)]">Radar</p>
        <h1 className="mt-2 text-3xl font-semibold">{grounded.length} oportunidades mais pe no chao</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">{stretch.length} ainda podem valer uma tentativa · selecionadas por adequacao, compatibilidade e localizacao</p>
        <div className="mt-5"><JobShortcuts active="for-me" /></div>
      </section>
      <HomeOpportunities grounded={grounded} stretch={stretch} />
    </div>
  );
}

async function loadHomeData() {
  try {
    return await getCuratedJobs({ view: "for-me", page: "1", page_size: "500", active: "true" });
  } catch {
    return null;
  }
}
