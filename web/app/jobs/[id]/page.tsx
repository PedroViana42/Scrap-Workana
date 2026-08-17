import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { JobDetail } from "@/components/jobs/job-detail";
import { ErrorState } from "@/components/ui/error-state";
import { RadarApiError, getJob } from "@/lib/radar-api";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  try {
    const job = await getJob(id);
    return { title: `${job.title}${job.company ? ` - ${job.company}` : ""} | Radar` };
  } catch {
    return { title: "Vaga | Radar" };
  }
}

export default async function JobDetailPage({ params }: PageProps) {
  const { id } = await params;
  const job = await loadJobOrNotFound(id);
  if (!job) {
    return <ErrorState message="Nao foi possivel carregar esta vaga agora." />;
  }
  return <JobDetail job={job} />;
}

async function loadJobOrNotFound(id: string) {
  try {
    return await getJob(id);
  } catch (error) {
    if (error instanceof RadarApiError && error.status === 404) {
      notFound();
    }
    return null;
  }
}
