import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AttainabilityExplanation } from "@/components/jobs/attainability-explanation";

describe("AttainabilityExplanation", () => {
  it("renders the human label and typed evidence", () => {
    render(<AttainabilityExplanation attainability={{ level: "HIGH", positive: ["Explicit junior role", "Mentorship provided"], warnings: [], negative: [] }} />);
    expect(screen.getByRole("heading", { name: "Adequacao ao momento" })).toBeInTheDocument();
    expect(screen.getByText(/Perfil de entrada/)).toBeInTheDocument();
    expect(screen.getByText(/Vaga Junior explicita/)).toBeInTheDocument();
    expect(screen.getByText(/Mentoria disponivel/)).toBeInTheDocument();
  });
});
