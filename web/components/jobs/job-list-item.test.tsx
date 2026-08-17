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
};

describe("JobListItem", () => {
  it("renders a dense job row with core fields", () => {
    render(<JobListItem job={job} />);
    expect(screen.getByRole("link", { name: "Backend Engineer" })).toHaveAttribute("href", "/jobs/1");
    expect(screen.getByText("Nubank")).toBeInTheDocument();
    expect(screen.getByText("Remoto")).toBeInTheDocument();
    expect(screen.getByText("Tempo integral")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
    expect(screen.getByText("96")).toBeInTheDocument();
  });
});
