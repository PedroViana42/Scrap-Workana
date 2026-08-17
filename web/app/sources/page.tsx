import { SourceList } from "@/components/sources/source-list";
import { ErrorState } from "@/components/ui/error-state";
import { formatNumber } from "@/lib/formatters";
import { getSources } from "@/lib/radar-api";

export const dynamic = "force-dynamic";

export default async function SourcesPage() {
  const sources = await loadSources();
  if (!sources) {
    return <ErrorState message="Nao foi possivel carregar as fontes agora." />;
  }
  return (
    <div className="space-y-5">
      <section>
        <h1 className="text-2xl font-semibold">Fontes</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">{formatNumber(sources.length)} fontes configuradas no Radar.</p>
      </section>
      <SourceList sources={sources} />
    </div>
  );
}

async function loadSources() {
  try {
    return await getSources();
  } catch {
    return null;
  }
}
