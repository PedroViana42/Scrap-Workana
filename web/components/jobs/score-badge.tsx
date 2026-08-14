import { formatBand, scoreTone } from "@/lib/formatters";

export function ScoreBadge({ score, band, compact = false }: { score: number | null; band: string | null; compact?: boolean }) {
  return (
    <div className={`text-right ${scoreTone(band)}`} aria-label={`Score ${score ?? "nao informado"} ${formatBand(band)}`}>
      <div className={compact ? "text-xl font-semibold leading-6" : "text-3xl font-semibold leading-8"}>{score ?? "-"}</div>
      <div className="text-[11px] font-semibold uppercase">{formatBand(band)}</div>
    </div>
  );
}
