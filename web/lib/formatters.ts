import type { RelevanceBand } from "@/lib/types";

const bandLabels: Record<string, string> = {
  excellent: "Excelente",
  strong: "Forte",
  interesting: "Interessante",
  low: "Baixa",
  very_low: "Muito baixa",
};

const employmentLabels: Record<string, string> = {
  full_time: "Tempo integral",
  part_time: "Meio periodo",
  internship: "Estagio",
  trainee: "Trainee",
  contract: "Contrato",
  temporary: "Temporario",
  unknown: "Nao informado",
};

const seniorityLabels: Record<string, string> = {
  intern: "Estagio",
  junior: "Junior",
  mid: "Pleno",
  senior: "Senior",
  lead: "Lead",
  unknown: "Nao informado",
};

const remoteLabels: Record<string, string> = {
  remote: "Remoto",
  hybrid: "Hibrido",
  onsite: "Presencial",
  unknown: "Nao informado",
};

export function formatBand(band: RelevanceBand | null | undefined): string {
  if (!band) return "Sem faixa";
  return bandLabels[String(band).toLowerCase()] ?? String(band);
}

export function scoreTone(band: RelevanceBand | null | undefined): string {
  const normalized = String(band ?? "").toLowerCase();
  if (normalized === "excellent") return "score-excellent";
  if (normalized === "strong") return "score-strong";
  if (normalized === "interesting") return "score-interesting";
  if (normalized === "low") return "score-low";
  if (normalized === "very_low") return "score-very_low";
  return "text-slate-600";
}

export function formatEmploymentType(value: string | null | undefined): string {
  if (!value) return "Nao informado";
  const normalized = value.toLowerCase();
  return employmentLabels[normalized] ?? value;
}

export function formatSeniority(value: string | null | undefined): string {
  if (!value) return "Nao informado";
  const normalized = value.toLowerCase();
  return seniorityLabels[normalized] ?? value;
}

export function formatRemoteType(value: string | null | undefined): string {
  if (!value) return "Nao informado";
  const normalized = value.toLowerCase();
  return remoteLabels[normalized] ?? value;
}

export function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat("pt-BR").format(value ?? 0);
}

export function formatRelativeDate(value: string | null | undefined): string {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "N/A";
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.max(0, Math.floor(diffMs / 60000));
  if (minutes < 1) return "agora";
  if (minutes < 60) return `ha ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `ha ${hours} h`;
  const days = Math.floor(hours / 24);
  return `ha ${days} dia${days === 1 ? "" : "s"}`;
}

export function formatLongDate(value: string | null | undefined): string {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "N/A";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
