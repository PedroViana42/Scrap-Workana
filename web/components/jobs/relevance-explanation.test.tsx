import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RelevanceExplanation } from "@/components/jobs/relevance-explanation";

describe("RelevanceExplanation", () => {
  it("renders product language without raw JSON", () => {
    const reasons = { positive: ["Matched Python", "Brazil eligible"], negative: ["Requires 3+ years experience"], matched_roles: ["SOFTWARE"] };
    const { container } = render(<RelevanceExplanation reasons={reasons} />);
    expect(screen.getByRole("heading", { name: "Por que combina" })).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Localizacao compativel com o Brasil")).toBeInTheDocument();
    expect(screen.getByText("Exige 3+ anos de experiencia")).toBeInTheDocument();
    expect(container).not.toHaveTextContent("matched_roles");
    expect(container.querySelector("pre")).toBeNull();
  });
});
