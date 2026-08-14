import type { JobListItem as JobListItemType } from "@/lib/types";
import { JobListItem } from "@/components/jobs/job-list-item";
import { EmptyState } from "@/components/ui/empty-state";

export function JobList({ jobs, clearHref }: { jobs: JobListItemType[]; clearHref: string }) {
  if (jobs.length === 0) {
    return <EmptyState clearHref={clearHref} />;
  }
  return (
    <div className="panel overflow-hidden">
      {jobs.map((job) => (
        <JobListItem job={job} key={job.id} />
      ))}
    </div>
  );
}
