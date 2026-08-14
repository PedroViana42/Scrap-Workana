export function Logo() {
  return (
    <span className="inline-flex items-center gap-2 text-lg font-semibold text-slate-950">
      <span aria-hidden className="relative flex h-6 w-6 items-center justify-center rounded-full border-2 border-slate-900">
        <span className="h-3.5 w-3.5 rounded-full border border-slate-900" />
        <span className="absolute h-1.5 w-1.5 rounded-full bg-slate-900" />
      </span>
      Radar
    </span>
  );
}
