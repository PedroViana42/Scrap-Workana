import type { RelevanceReasons } from "@/lib/types";

export function RelevanceExplanation({ reasons }: { reasons: RelevanceReasons | null }) {
  const positive = unique(reasons?.positive).map(humanizeSignal);
  const attention = unique(reasons?.negative).map(humanizeSignal);
  if (!positive.length && !attention.length) return null;
  return (
    <section className="grid gap-4 md:grid-cols-2" aria-label="Explicacao da relevancia">
      {positive.length ? <SignalGroup title="Pontos de compatibilidade" items={positive} symbol="✓" tone="positive" /> : null}
      {attention.length ? <SignalGroup title="Requisitos a considerar" items={attention} symbol="!" tone="warning" /> : null}
    </section>
  );
}

function SignalGroup({ title, items, symbol, tone }: { title: string; items: string[]; symbol: string; tone: "positive" | "warning" }) {
  return (
    <div className={`signal-group signal-${tone}`}>
      <h2 className="text-base font-semibold">{title}</h2>
      <ul className="mt-3 space-y-2">
        {items.map((item) => <li className="flex gap-2 text-sm" key={item}><span aria-hidden="true" className="font-bold">{symbol}</span><span>{item}</span></li>)}
      </ul>
    </div>
  );
}

function unique(value: unknown): string[] {
  return Array.isArray(value) ? [...new Set(value.filter((item): item is string => typeof item === "string"))] : [];
}

export function humanizeSignal(signal: string): string {
  const exact: Record<string, string> = {
    "Early-career title": "Titulo compativel com inicio de carreira",
    "Fresh posting": "Publicada recentemente",
    "Software role": "Area de software compativel",
    "Backend role": "Area de backend compativel",
    "Brazil eligible": "Localizacao compativel com o Brasil",
    "LATAM includes Brazil": "Remota para LATAM",
    "Americas remote": "Remota para as Americas",
    "Worldwide/global remote": "Remota mundial",
    "Remote role, geography unknown": "Remota, mas com elegibilidade geografica incerta",
    "Level II/III title": "Nivel II/III pode exigir mais experiencia",
    "Senior-level role": "Nivel senior acima do perfil priorizado",
    "Location eligibility unclear": "Elegibilidade para o Brasil nao esta clara",
    "Foreign location: on-site outside Brazil": "Presencial fora do Brasil",
  };
  if (exact[signal]) return exact[signal];
  if (signal.startsWith("Matched ")) return signal.slice(8);
  if (/^Requires \d+\+ years experience$/.test(signal)) return signal.replace("Requires", "Exige").replace("years experience", "anos de experiencia");
  return signal
    .replace("Foreign location, Brazil eligibility unknown", "Localizacao estrangeira; elegibilidade para o Brasil incerta")
    .replace("Foreign location with remote eligibility restricted", "Remota restrita a outra regiao")
    .replace(" role", " compativel");
}
