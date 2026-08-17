import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "@/components/ui/empty-state";

describe("EmptyState", () => {
  it("offers a clear filters link", () => {
    render(<EmptyState clearHref="/jobs" />);
    expect(screen.getByText("Nenhuma vaga encontrada.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Limpar filtros" })).toHaveAttribute("href", "/jobs");
  });
});
