import { AttainabilityBadge } from "@/components/jobs/attainability-badge";
import type { Attainability } from "@/lib/types";

const translations: Record<string, string> = {
  "Explicit junior role": "Vaga Junior explicita",
  "Graduate role": "Vaga para recem-formados",
  "Internship role": "Vaga de estagio",
  "Accepts recent graduates": "Aceita recem-formados",
  "0-1 years experience": "0–1 ano de experiencia",
  "1-2 years experience": "1–2 anos de experiencia",
  "2-3 years experience": "2–3 anos de experiencia",
  "No prior professional experience required": "Nao exige experiencia profissional anterior",
  "Mentorship provided": "Mentoria disponivel",
  "Mid-level title": "Titulo de nivel intermediario",
  "Senior-level title": "Titulo senior",
  "Technical leadership responsibility": "Responsabilidade de lideranca tecnica",
  "Independent production ownership": "Autonomia sobre sistemas em producao",
  "On-call ownership expected": "Responsabilidade por plantao esperada",
};

function humanize(signal: string) {
  return translations[signal] ?? signal.replace(/^Requires /, "Exige ");
}

export function AttainabilityExplanation({ attainability }: { attainability: Attainability }) {
  const compatible = attainability.positive.map(humanize);
  const requirements = [...attainability.warnings, ...attainability.negative].map(humanize);
  return (
    <div>
      <h2 className="text-lg font-semibold">Compatibilidade de experiencia</h2>
      <div className="mt-3"><AttainabilityBadge level={attainability.level} /></div>
      {compatible.length ? <EvidenceGroup title="Pontos de compatibilidade" items={compatible} /> : null}
      {requirements.length ? <EvidenceGroup title="Requisitos a considerar" items={requirements} /> : null}
    </div>
  );
}

function EvidenceGroup({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-3">
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <ul className="mt-1 space-y-1 text-sm text-[var(--muted)]">
        {items.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}
