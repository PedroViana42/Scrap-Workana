export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="panel overflow-hidden">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="border-b border-[var(--border-muted)] p-4" key={index}>
          <div className="h-4 w-1/3 rounded bg-slate-200" />
          <div className="mt-3 h-3 w-2/3 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}

export function ListSkeleton() {
  return <SkeletonRows rows={5} />;
}
