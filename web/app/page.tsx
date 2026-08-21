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
        <h1 className="text-3xl font-semibold">Radar</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">{grounded.length} oportunidades recomendadas · {stretch.length} oportunidades com experiencia intermediaria</p>
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
