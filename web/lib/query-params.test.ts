import { describe, expect, it } from "vitest";
import { activeFilters, hrefWithParams, normalizeSearchParams, removeFilterHref } from "@/lib/query-params";

describe("query params", () => {
  it("normalizes supported params and ignores unknown keys", () => {
    expect(normalizeSearchParams({ q: "python", page: ["2"], ignored: "x" })).toEqual({ q: "python", page: "2" });
  });

  it("creates hrefs from active params and updates", () => {
    expect(hrefWithParams("/jobs", { q: "python", page: "2" }, { page: "3" })).toBe("/jobs?q=python&page=3");
  });

  it("removes one active filter and resets page", () => {
    expect(removeFilterHref("/jobs", { q: "python", page: "4", remote: "true" }, "remote")).toBe("/jobs?q=python&page=1");
  });

  it("keeps default active=true out of filter chips", () => {
    expect(activeFilters({ active: "true", technology: "Python" })).toEqual([{ key: "technology", label: "Tecnologia: Python", value: "Python" }]);
  });
});
