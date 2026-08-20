import type { Attainability } from "@/lib/types";

const labels: Record<Attainability["level"], string> = {
  HIGH: "Perfil de entrada",
  MEDIUM: "Stretch",
  LOW: "Avancada",
};

export function AttainabilityBadge({ level }: { level: Attainability["level"] }) {
  const styles = level === "HIGH"
    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
    : level === "MEDIUM"
      ? "border-amber-200 bg-amber-50 text-amber-800"
      : "border-slate-200 bg-slate-100 text-slate-700";
  return <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${styles}`}>{level === "HIGH" ? "🎯 " : level === "MEDIUM" ? "🚀 " : ""}{labels[level]}</span>;
}
