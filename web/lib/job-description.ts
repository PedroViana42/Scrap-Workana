import sanitizeHtml from "sanitize-html";

const ALLOWED_TAGS = ["h2", "h3", "h4", "p", "ul", "ol", "li", "strong", "b", "em", "i", "a", "br", "blockquote"];

export function sanitizeJobDescription(description: string | null | undefined): string {
  if (!description?.trim()) return "";
  const source = looksLikeHtml(description) ? description : plainTextToHtml(description);
  return sanitizeHtml(source, {
    allowedTags: ALLOWED_TAGS,
    allowedAttributes: { a: ["href", "title", "target", "rel"] },
    allowedSchemes: ["http", "https", "mailto"],
    allowProtocolRelative: false,
    disallowedTagsMode: "discard",
    transformTags: {
      a: (_tagName, attribs) => ({
        tagName: "a",
        attribs: {
          ...attribs,
          target: "_blank",
          rel: "noopener noreferrer nofollow",
        },
      }),
    },
  });
}

function looksLikeHtml(value: string): boolean {
  return /<\/?[a-z][\s\S]*>/i.test(value);
}

function plainTextToHtml(value: string): string {
  return value
    .replace(/\r/g, "")
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${escapeHtml(paragraph.trim()).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
