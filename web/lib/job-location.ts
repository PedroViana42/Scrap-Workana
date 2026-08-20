import type { JobListItem, JobView } from "@/lib/types";

export const LOCAL_REGION = {
  label: "Goiania e regiao",
  municipalities: ["Goiânia", "Aparecida de Goiânia", "Senador Canedo", "Trindade", "Goianira"],
} as const;

export type WorkMode = "remote" | "hybrid" | "onsite" | "unknown";
export type RemoteEligibility = "brazil" | "latam" | "south-america" | "americas" | "worldwide" | "unclear" | "restricted" | "not-remote";

const LOCAL_TERMS = ["goiania", "aparecida de goiania", "senador canedo", "trindade", "goianira"];
const RESTRICTED_REMOTE = [
  /\b(us|usa|united states)\s*(only|based|remote)\b/,
  /\bremote\s*[-–—,:]?\s*(us|usa|united states)\b/,
  /\b(eu|europe|uk|united kingdom|ireland)\s*only\b/,
];

export function normalizeLocation(value: string | null | undefined): string {
  return (value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function getWorkMode(job: Pick<JobListItem, "location" | "remote" | "remote_type">): WorkMode {
  const declared = normalizeLocation(job.remote_type);
  const location = normalizeLocation(job.location);
  if (declared.includes("hybrid") || declared.includes("hibrid")) return "hybrid";
  if (declared.includes("onsite") || declared.includes("on site") || declared.includes("presencial")) return "onsite";
  if (declared === "remote" || declared.includes("remoto") || job.remote) return "remote";
  if (/\b(remote|remoto|home based|work from home|worldwide|global)\b/.test(location)) return "remote";
  return "unknown";
}

export function isLocalRegion(location: string | null | undefined): boolean {
  const normalized = normalizeLocation(location);
  return LOCAL_TERMS.some((term) => normalized.includes(term));
}

export function remoteEligibility(job: Pick<JobListItem, "location" | "remote" | "remote_type">): RemoteEligibility {
  if (getWorkMode(job) !== "remote") return "not-remote";
  const location = normalizeLocation(job.location);
  if (RESTRICTED_REMOTE.some((pattern) => pattern.test(location))) return "restricted";
  if (/\b(brazil|brasil)\b/.test(location)) return "brazil";
  if (/\b(latam|latin america|america latina)\b/.test(location)) return "latam";
  if (/\b(south america|america do sul)\b/.test(location)) return "south-america";
  if (/\bamericas?\b/.test(location)) return "americas";
  if (/\b(worldwide|global|globally)\b/.test(location)) return "worldwide";
  return "unclear";
}

export function isBrazilCompatibleRemote(job: Pick<JobListItem, "location" | "remote" | "remote_type">): boolean {
  return ["brazil", "latam", "south-america", "americas", "worldwide"].includes(remoteEligibility(job));
}

export function isForMe(job: JobListItem): boolean {
  const band = String(job.relevance_band ?? "").toLowerCase();
  if (!["excellent", "strong", "interesting"].includes(band)) return false;
  const mode = getWorkMode(job);
  return isBrazilCompatibleRemote(job) || ((mode === "hybrid" || mode === "onsite") && isLocalRegion(job.location));
}

export function matchesJobView(job: JobListItem, view: JobView): boolean {
  if (view === "for-me") return isForMe(job);
  if (view === "goiania") return (getWorkMode(job) === "hybrid" || getWorkMode(job) === "onsite") && isLocalRegion(job.location);
  if (view === "remote") return remoteEligibility(job) !== "restricted" && remoteEligibility(job) !== "not-remote";
  const location = normalizeLocation(job.location);
  return /\b(brazil|brasil)\b/.test(location) || isBrazilCompatibleRemote(job);
}

export function formatJobLocation(job: Pick<JobListItem, "location" | "remote" | "remote_type">): string[] {
  const mode = getWorkMode(job);
  const eligibility = remoteEligibility(job);
  let location = job.location?.trim() || "";
  if (mode === "remote") {
    const labels: Partial<Record<RemoteEligibility, string>> = {
      brazil: "Brasil",
      latam: "LATAM",
      "south-america": "America do Sul",
      americas: "Americas",
      worldwide: "Worldwide",
    };
    location = labels[eligibility] ?? location;
  }
  const modeLabel = mode === "remote"
    ? eligibility === "unclear" ? "Remoto · elegibilidade incerta" : eligibility === "restricted" ? "Remoto · restrito" : "Remoto"
    : { hybrid: "Hibrido", onsite: "Presencial", unknown: "" }[mode];
  return [location, modeLabel].filter(Boolean);
}
