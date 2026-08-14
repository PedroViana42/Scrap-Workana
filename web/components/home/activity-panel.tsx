import { formatLongDate, formatNumber } from "@/lib/formatters";
import type { StatsResponse } from "@/lib/types";

export function ActivityPanel({ stats }: { stats: StatsResponse }) {
  const runs = stats.scrape_runs_24h ?? {};
  return (
    <aside className="panel p-4">
      <h2 className="text-base font-semibold">Atividade do Radar</h2>
      <dl className="mt-4 space-y-3 text-sm">
        <Row label="Ultima coleta" value={formatLongDate(stats.last_successful_scrape)} />
        <Row label="Fontes habilitadas" value={formatNumber(stats.sources_enabled)} />
        <Row label="Empresas monitoradas" value={formatNumber(stats.company_sources_enabled)} />
        <Row label="Vagas ativas" value={formatNumber(stats.jobs_active)} />
        {Object.entries(runs).map(([status, count]) => (
          <Row key={status} label={`Coletas 24h: ${status}`} value={formatNumber(count)} />
        ))}
      </dl>
    </aside>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}
