import Link from "next/link";

export function EmptyState({ clearHref = "/jobs" }: { clearHref?: string }) {
  return (
    <div className="panel flex min-h-48 flex-col items-center justify-center gap-2 p-8 text-center">
      <h2 className="text-base font-semibold">Nenhuma vaga encontrada.</h2>
      <p className="text-sm text-[var(--muted)]">Tente remover alguns filtros.</p>
      <Link className="mt-2 rounded-md border border-[var(--border)] px-3 py-1.5 text-sm font-medium hover:bg-slate-50" href={clearHref}>
        Limpar filtros
      </Link>
    </div>
  );
}
