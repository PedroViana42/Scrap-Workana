import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { JobListItem } from "@/components/jobs/job-list-item";
import type { JobListItem as Job } from "@/lib/types";

const job: Job = {
  id: 1,
  title: "Backend Engineer",
  company: "Nubank",
  source: "greenhouse",
  url: "https://example.com",
  location: "Brazil",
  remote: true,
  remote_type: "remote",
  employment_type: "full_time",
  seniority: "mid",
  technologies: ["Python", "FastAPI", "PostgreSQL", "Docker", "Kafka"],
  published_at: "2026-08-14T10:00:00Z",
  first_seen_at: "2026-08-14T10:10:00Z",
  last_seen_at: "2026-08-14T10:10:00Z",
  relevance_score: 96,
  relevance_band: "excellent",
  attainability: { level: "HIGH", positive: ["Explicit junior role"], warnings: [], negative: [] },
};

describe("JobListItem", () => {
  it("renders a concise remote job card with core fields", () => {
    render(<JobListItem job={job} />);
    expect(screen.getByRole("link", { name: "Backend Engineer" })).toHaveAttribute("href", "/jobs/1");
    expect(screen.getByText("Nubank")).toBeInTheDocument();
    expect(screen.getByText("Remoto")).toBeInTheDocument();
    expect(screen.getByText("Tempo integral")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
    expect(screen.getByText("96")).toBeInTheDocument();
    expect(screen.getByText(/Perfil de entrada/)).toBeInTheDocument();
  });

  it("omits unavailable placeholders", () => {
    render(<JobListItem job={{ ...job, location: null, remote: false, remote_type: "unknown", employment_type: "unknown", published_at: null }} />);
    expect(screen.queryByText("Nao informado")).not.toBeInTheDocument();
    expect(screen.queryByText(/N\/A/)).not.toBeInTheDocument();
  });

  it.each([
    ["hybrid", "Hibrido"],
    ["onsite", "Presencial"],
  ])("renders a Goiania %s job", (remoteType, label) => {
    render(<JobListItem job={{ ...job, location: "Goiânia, GO", remote: false, remote_type: remoteType }} />);
    expect(screen.getByText("Goiânia, GO")).toBeInTheDocument();
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});
