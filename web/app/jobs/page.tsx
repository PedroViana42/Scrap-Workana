import { JobFilters } from "@/components/jobs/filters";
import { JobList } from "@/components/jobs/job-list";
import { Pagination } from "@/components/jobs/pagination";
import { ErrorState } from "@/components/ui/error-state";
import { formatNumber } from "@/lib/formatters";
import { normalizeSearchParams } from "@/lib/query-params";
import { getCuratedJobs, getJobs, getSources } from "@/lib/radar-api";

export const dynamic = "force-dynamic";

type PageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function JobsPage({ searchParams }: PageProps) {
  const params = normalizeSearchParams(await searchParams);
  const listParams = {
    ...params,
    page: params.page ?? "1",
    page_size: params.page_size ?? "20",
    active: params.active ?? "true",
  };
  const data = await loadJobsData(listParams);
  if (!data) {
    return <ErrorState message="Nao foi possivel carregar as vagas agora." />;
  }
  const [jobs, sources] = data;

  return (
    <div className="space-y-5">
      <section className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold">Vagas</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">{formatNumber(jobs.total)} oportunidades encontradas</p>
        </div>
        <JobFilters params={listParams} sources={sources} />
      </section>

      <section>
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">{formatNumber(jobs.total)} resultados</h2>
          <div className="rounded-md border border-[var(--border)] bg-white px-3 py-1.5 text-sm text-[var(--muted)]">Mais relevantes</div>
        </div>
        <JobList jobs={jobs.items} clearHref="/jobs" />
        <Pagination page={jobs.page} pages={jobs.pages} params={listParams} />
      </section>
    </div>
  );
}

async function loadJobsData(params: ReturnType<typeof normalizeSearchParams>) {
  try {
    return await Promise.all([params.view ? getCuratedJobs({ ...params, view: params.view }) : getJobs(params), getSources()]);
  } catch {
    return null;
  }
}
