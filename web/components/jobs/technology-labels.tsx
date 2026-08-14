export function TechnologyLabels({ technologies, limit = 4 }: { technologies: string[]; limit?: number }) {
  const visible = technologies.slice(0, limit);
  const hidden = Math.max(0, technologies.length - visible.length);
  if (technologies.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {visible.map((technology) => (
        <span className="label" key={technology}>
          {technology}
        </span>
      ))}
      {hidden > 0 ? <span className="label">+{hidden}</span> : null}
    </div>
  );
}
