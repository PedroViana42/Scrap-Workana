import Link from "next/link";
import type { JobView } from "@/lib/types";

const shortcuts: Array<{ view: JobView; label: string }> = [
  { view: "for-me", label: "Para mim" },
  { view: "brazil", label: "Brasil" },
  { view: "remote", label: "Remotas" },
  { view: "goiania", label: "Goiania" },
];

export function JobShortcuts({ active }: { active?: JobView }) {
  return <nav aria-label="Atalhos de vagas" className="flex flex-wrap gap-2">{shortcuts.map(({ view, label }) => <Link aria-current={active === view ? "page" : undefined} className={`shortcut-chip ${active === view ? "shortcut-chip-active" : ""}`} href={`/jobs?view=${view}`} key={view}>{label}</Link>)}</nav>;
}
