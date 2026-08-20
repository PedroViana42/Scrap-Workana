import { describe, expect, it } from "vitest";
import { formatJobLocation, homeGroupForJob, isForMe, isLocalRegion, matchesJobView, remoteEligibility } from "@/lib/job-location";
import type { JobListItem } from "@/lib/types";

const base: JobListItem = {
  id: 1, title: "Software Engineer", company: "Acme", source: "test", url: "https://example.com",
  location: null, remote: false, remote_type: "unknown", employment_type: "full_time", seniority: "junior",
  technologies: ["Python"], published_at: null, first_seen_at: "2026-08-20T00:00:00Z", last_seen_at: "2026-08-20T00:00:00Z",
  relevance_score: 80, relevance_band: "STRONG",
  attainability: { level: "HIGH", positive: [], warnings: [], negative: [] },
};

const job = (location: string, remote_type: string, remote = remote_type === "remote") => ({ ...base, location, remote_type, remote });

describe("job geography", () => {
  it.each(["Goiânia", "Goiania - GO", "Aparecida de Goiânia", "Senador Canedo", "Trindade", "Goianira"])("recognizes local municipality %s", (location) => {
    expect(isLocalRegion(location)).toBe(true);
  });

  it("includes hybrid and onsite local jobs in Para mim", () => {
    expect(isForMe(job("Goiânia, GO", "hybrid"))).toBe(true);
    expect(isForMe(job("Aparecida de Goiânia", "onsite"))).toBe(true);
  });

  it("rejects hybrid and onsite jobs outside the local region from Para mim", () => {
    expect(isForMe(job("São Paulo, SP", "hybrid"))).toBe(false);
    expect(isForMe(job("Rio de Janeiro, RJ", "onsite"))).toBe(false);
  });

  it("does not invent a physical modality for an unknown Goiania job", () => {
    const candidate = job("Goiânia, GO", "unknown", false);
    expect(isForMe(candidate)).toBe(false);
    expect(matchesJobView(candidate, "goiania")).toBe(false);
  });

  it.each([
    ["Remote - Brazil", "brazil"],
    ["LATAM Remote", "latam"],
    ["South America - Remote", "south-america"],
    ["Americas Remote", "americas"],
    ["Home based - Worldwide", "worldwide"],
  ] as const)("accepts compatible remote geography %s", (location, eligibility) => {
    const candidate = job(location, "remote");
    expect(remoteEligibility(candidate)).toBe(eligibility);
    expect(isForMe(candidate)).toBe(true);
  });

  it("keeps generic remote uncertain and outside Para mim", () => {
    const candidate = job("Remote", "remote");
    expect(remoteEligibility(candidate)).toBe("unclear");
    expect(isForMe(candidate)).toBe(false);
    expect(matchesJobView(candidate, "remote")).toBe(true);
    expect(formatJobLocation(candidate)).toContain("Remoto · elegibilidade incerta");
  });

  it("does not treat Remote US as Brazil-compatible", () => {
    const candidate = job("Remote - US only", "remote");
    expect(remoteEligibility(candidate)).toBe("restricted");
    expect(isForMe(candidate)).toBe(false);
    expect(matchesJobView(candidate, "remote")).toBe(false);
    expect(formatJobLocation(candidate)).toContain("Remoto · restrito");
  });

  it.each([
    ["HIGH", "interesting", "grounded"],
    ["HIGH", "low", null],
    ["MEDIUM", "strong", "stretch"],
    ["MEDIUM", "interesting", null],
    ["LOW", "excellent", null],
  ] as const)("classifies %s / %s for the Home", (level, relevance_band, expected) => {
    const candidate = { ...job("Remote Brazil", "remote"), relevance_band, attainability: { level, positive: [], warnings: [], negative: [] } };
    expect(homeGroupForJob(candidate)).toBe(expected);
  });

  it("excludes LOW from Para mim even with an excellent score", () => {
    const candidate = { ...job("Worldwide", "remote"), relevance_band: "excellent", attainability: { level: "LOW" as const, positive: [], warnings: [], negative: [] } };
    expect(isForMe(candidate)).toBe(false);
  });
});
