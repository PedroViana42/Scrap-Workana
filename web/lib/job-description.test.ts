import { describe, expect, it } from "vitest";
import { sanitizeJobDescription } from "@/lib/job-description";

describe("sanitizeJobDescription", () => {
  it("preserves useful job description semantics", () => {
    const result = sanitizeJobDescription('<h3>Role</h3><p>Build <strong>APIs</strong>.</p><ul><li>Python</li></ul><a href="https://example.com/job">Details</a>');
    expect(result).toContain("<h3>Role</h3>");
    expect(result).toContain("<strong>APIs</strong>");
    expect(result).toContain("<li>Python</li>");
    expect(result).toContain('rel="noopener noreferrer nofollow"');
    expect(result).toContain('target="_blank"');
  });

  it("removes scripts, handlers, iframes and unsafe links", () => {
    const result = sanitizeJobDescription('<script>alert(1)</script><p onclick="steal()">Safe</p><iframe src="https://bad.test"></iframe><a href="javascript:alert(1)">Bad</a>');
    expect(result).toContain("<p>Safe</p>");
    expect(result).not.toMatch(/script|onclick|iframe|javascript:/i);
  });
});
