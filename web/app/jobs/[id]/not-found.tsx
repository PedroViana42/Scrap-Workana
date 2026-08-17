import Link from "next/link";

export default function NotFound() {
  return (
    <div className="panel flex min-h-48 flex-col items-center justify-center gap-3 p-8 text-center">
      <h1 className="text-lg font-semibold">Vaga nao encontrada.</h1>
      <Link className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm font-medium hover:bg-slate-50" href="/jobs">
        Voltar para vagas
      </Link>
    </div>
  );
}
