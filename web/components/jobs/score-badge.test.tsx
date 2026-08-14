import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreBadge } from "@/components/jobs/score-badge";

describe("ScoreBadge", () => {
  it("shows score and band", () => {
    render(<ScoreBadge score={96} band="excellent" />);
    expect(screen.getByText("96")).toBeInTheDocument();
    expect(screen.getByText("Excelente")).toBeInTheDocument();
  });

  it("handles missing scores", () => {
    render(<ScoreBadge score={null} band={null} />);
    expect(screen.getByText("-")).toBeInTheDocument();
    expect(screen.getByText("Sem faixa")).toBeInTheDocument();
  });
});
