import { sanitizeJobDescription } from "@/lib/job-description";

export function JobDescription({ description }: { description: string | null }) {
  const html = sanitizeJobDescription(description);
  if (!html) return <p className="text-sm text-[var(--muted)]">A fonte nao forneceu uma descricao.</p>;
  return <div className="job-description" dangerouslySetInnerHTML={{ __html: html }} />;
}
