import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Pagination } from "@/components/jobs/pagination";

describe("Pagination", () => {
  it("links to previous and next pages", () => {
    render(<Pagination page={2} pages={4} params={{ q: "python", page: "2" }} />);
    expect(screen.getByRole("link", { name: "Anterior" })).toHaveAttribute("href", "/jobs?q=python&page=1");
    expect(screen.getByRole("link", { name: "Proxima" })).toHaveAttribute("href", "/jobs?q=python&page=3");
    expect(screen.getByText("de 4")).toBeInTheDocument();
  });
});
