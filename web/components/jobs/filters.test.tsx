import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { JobFilters } from "@/components/jobs/filters";

describe("JobFilters", () => {
  it("renders search, filter controls and active chips", () => {
    render(<JobFilters params={{ q: "python", remote: "true", technology: "FastAPI" }} sources={[{ name: "greenhouse", display_name: "Greenhouse", content_type: "job", enabled: true, status: "active", collector: "greenhouse", priority: 10 }]} />);
    expect(screen.getByPlaceholderText("Buscar por cargo, empresa ou tecnologia...")).toHaveValue("python");
    expect(screen.getByRole("button", { name: "Buscar" })).toBeInTheDocument();
    expect(screen.getByLabelText("Nivel da oportunidade")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Remoto x" })).toHaveAttribute("href", "/jobs?q=python&technology=FastAPI&page=1");
    expect(screen.getByRole("link", { name: "Tecnologia: FastAPI x" })).toBeInTheDocument();
  });
});
