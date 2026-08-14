import Link from "next/link";
import { Logo } from "@/components/layout/logo";

export function Header() {
  return (
    <header className="border-b border-[var(--border)] bg-white">
      <div className="container-shell flex h-14 items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" aria-label="Radar home">
            <Logo />
          </Link>
          <nav aria-label="Principal" className="hidden h-14 items-center gap-1 sm:flex">
            <Link className="flex h-14 items-center border-b-2 border-transparent px-4 font-medium hover:border-[var(--blue)]" href="/jobs">
              Vagas
            </Link>
            <Link className="flex h-14 items-center border-b-2 border-transparent px-4 font-medium hover:border-[var(--blue)]" href="/sources">
              Fontes
            </Link>
          </nav>
        </div>
        <nav aria-label="Principal mobile" className="flex gap-2 sm:hidden">
          <Link className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm font-medium" href="/jobs">
            Vagas
          </Link>
          <Link className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm font-medium" href="/sources">
            Fontes
          </Link>
        </nav>
      </div>
    </header>
  );
}
