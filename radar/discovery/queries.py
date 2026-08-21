from dataclasses import dataclass


LOCAL_AREAS = (
    "Goiânia",
    "Aparecida de Goiânia",
    "Senador Canedo",
    "Trindade",
    "Goianira",
)

DEFAULT_LOCAL_QUERIES = (
    '"Goiânia" "desenvolvedor júnior"',
    '"Goiânia" (backend OR frontend OR "full stack") vaga',
    '"Goiânia" (Java OR Python OR .NET OR TypeScript) vaga',
    '"Goiânia" "estágio desenvolvimento"',
    '"Goiânia" "estágio TI"',
    '"Goiânia" ("analista de dados" OR BI)',
    '"Goiânia" ("ciência de dados" OR "engenharia de dados")',
    '"Goiânia" (IA OR automação) vaga',
    '"Goiânia" (DevOps OR infraestrutura) vaga',
    '"Goiânia" ("suporte TI" OR "analista de sistemas" OR QA)',
    '"Aparecida de Goiânia" (desenvolvedor OR "suporte TI" OR estágio)',
    '"Senador Canedo" (TI OR sistemas OR dados) vaga',
    '"Trindade" (TI OR desenvolvedor OR suporte) vaga',
    '"Goianira" (TI OR desenvolvedor OR suporte) vaga',
    'site:linkedin.com/jobs "Goiânia" (desenvolvedor OR dados OR TI)',
    'site:gupy.io/jobs "Goiânia" (tecnologia OR dados OR sistemas)',
    'site:zohopublic.com "Goiânia" (desenvolvedor OR TI)',
    'site:solides.com.br/vaga "Goiânia" (tecnologia OR suporte OR dados)',
)


@dataclass(frozen=True)
class LocalDiscoveryQuerySet:
    queries: tuple[str, ...] = DEFAULT_LOCAL_QUERIES

    def iter_queries(self):
        yield from self.queries
