import { formatNumber } from "@/lib/formatters";

export function StatCard({ label, value, hint, tone = "default" }: { label: string; value: number; hint?: string; tone?: "default" | "green" | "blue" | "amber" }) {
  const toneClass = tone === "green" ? "text-[var(--green)]" : tone === "blue" ? "text-[var(--blue)]" : tone === "amber" ? "text-[var(--amber)]" : "text-slate-950";
  return (
    <div className="panel p-4">
      <div className="text-xs font-semibold uppercase text-[var(--muted)]">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${toneClass}`}>{formatNumber(value)}</div>
      {hint ? <div className="mt-1 text-sm text-[var(--muted)]">{hint}</div> : null}
    </div>
  );
}
