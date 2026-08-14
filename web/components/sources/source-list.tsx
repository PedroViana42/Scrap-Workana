import type { SourceItem } from "@/lib/types";

export function SourceList({ sources }: { sources: SourceItem[] }) {
  return (
    <div className="panel overflow-hidden">
      {sources.map((source) => (
        <article className="grid gap-3 border-b border-[var(--border-muted)] p-4 last:border-b-0 md:grid-cols-[1fr_160px_120px]" key={source.name}>
          <div>
            <h2 className="font-semibold">{source.display_name}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">{source.name}</p>
          </div>
          <div className="text-sm">
            <div className="text-xs font-semibold uppercase text-[var(--muted)]">Collector</div>
            <div>{source.collector ?? "N/A"}</div>
          </div>
          <div className="text-sm">
            <span className={`label ${source.enabled ? "text-[var(--green)]" : "text-[var(--red)]"}`}>{source.enabled ? "Habilitada" : "Desabilitada"}</span>
            <div className="mt-2 text-xs text-[var(--muted)]">Prioridade {source.priority}</div>
          </div>
        </article>
      ))}
    </div>
  );
}
