import { describe, expect, it, vi } from "vitest";
import { formatBand, formatEmploymentType, formatNumber, formatRelativeDate, scoreTone } from "@/lib/formatters";

describe("formatters", () => {
  it("formats relevance bands and score tones", () => {
    expect(formatBand("excellent")).toBe("Excelente");
    expect(formatBand("strong")).toBe("Forte");
    expect(scoreTone("interesting")).toBe("score-interesting");
    expect(scoreTone(null)).toBe("text-slate-600");
  });

  it("formats common enum values", () => {
    expect(formatEmploymentType("full_time")).toBe("Tempo integral");
    expect(formatEmploymentType("FULL_TIME")).toBe("Tempo integral");
    expect(formatEmploymentType(undefined)).toBe("Nao informado");
  });

  it("formats numbers for pt-BR", () => {
    expect(formatNumber(7411)).toBe("7.411");
  });

  it("formats relative dates", () => {
    vi.setSystemTime(new Date("2026-08-14T12:00:00Z"));
    expect(formatRelativeDate("2026-08-14T11:30:00Z")).toBe("ha 30 min");
    expect(formatRelativeDate("2026-08-12T12:00:00Z")).toBe("ha 2 dias");
    vi.useRealTimers();
  });
});
