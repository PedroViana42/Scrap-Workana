import Link from "next/link";
import type { JobSearchParams } from "@/lib/types";
import { hrefWithParams } from "@/lib/query-params";

export function Pagination({ page, pages, params }: { page: number; pages: number; params: JobSearchParams }) {
  if (pages <= 1) return null;
  const previous = Math.max(1, page - 1);
  const next = Math.min(pages, page + 1);
  return (
    <nav aria-label="Paginacao" className="mt-4 flex items-center justify-center gap-2">
      <Link aria-disabled={page <= 1} className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm aria-disabled:pointer-events-none aria-disabled:opacity-50" href={hrefWithParams("/jobs", params, { page: String(previous) })}>
        Anterior
      </Link>
      <span className="rounded-md border border-[var(--blue)] bg-[var(--blue)] px-3 py-1.5 text-sm font-semibold text-white">{page}</span>
      <span className="text-sm text-[var(--muted)]">de {pages}</span>
      <Link aria-disabled={page >= pages} className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm aria-disabled:pointer-events-none aria-disabled:opacity-50" href={hrefWithParams("/jobs", params, { page: String(next) })}>
        Proxima
      </Link>
    </nav>
  );
}
