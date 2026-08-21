import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HomeOpportunities } from "@/components/home/home-opportunities";
import type { JobListItem } from "@/lib/types";

const stretch: JobListItem = {
  id: 2, title: "Software Engineer", company: "Acme", source: "test", url: "https://example.com",
  location: "Brazil", remote: true, remote_type: "remote", employment_type: "full_time", seniority: "mid",
  technologies: ["Python"], published_at: null, first_seen_at: "2026-08-20T00:00:00Z", last_seen_at: "2026-08-20T00:00:00Z",
  relevance_score: 88, relevance_band: "strong", attainability: { level: "MEDIUM", positive: [], warnings: ["2-3 years experience"], negative: [] },
};

describe("HomeOpportunities", () => {
  it("keeps compatible opportunities visible when there are no HIGH jobs", () => {
    render(<HomeOpportunities grounded={[]} stretch={[stretch]} />);
    expect(screen.getByText("Nenhuma oportunidade recomendada no momento.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver todas as vagas" })).toHaveAttribute("href", "/jobs");
    expect(screen.getByRole("heading", { name: "Outras oportunidades compativeis" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Software Engineer" })).toBeInTheDocument();
  });
});
