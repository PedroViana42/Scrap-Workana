import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AttainabilityExplanation } from "@/components/jobs/attainability-explanation";

describe("AttainabilityExplanation", () => {
  it("renders the human label and typed evidence", () => {
    render(<AttainabilityExplanation attainability={{ level: "HIGH", positive: ["Explicit junior role", "Mentorship provided"], warnings: [], negative: [] }} />);
    expect(screen.getByRole("heading", { name: "Compatibilidade de experiencia" })).toBeInTheDocument();
    expect(screen.getByText("Inicio de carreira")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pontos de compatibilidade" })).toBeInTheDocument();
    expect(screen.getByText(/Vaga Junior explicita/)).toBeInTheDocument();
    expect(screen.getByText(/Mentoria disponivel/)).toBeInTheDocument();
  });

  it("separates intermediate requirements from compatibility evidence", () => {
    render(<AttainabilityExplanation attainability={{ level: "MEDIUM", positive: [], warnings: ["2-3 years experience"], negative: ["Independent production ownership"] }} />);
    expect(screen.getByText("Experiencia intermediaria")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Requisitos a considerar" })).toBeInTheDocument();
    expect(screen.getByText(/2–3 anos de experiencia/)).toBeInTheDocument();
    expect(screen.getByText(/Autonomia sobre sistemas em producao/)).toBeInTheDocument();
  });
});
