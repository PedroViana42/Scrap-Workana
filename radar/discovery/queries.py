from dataclasses import dataclass


LOCAL_AREAS = (
    "Goiânia",
    "Aparecida de Goiânia",
    "Senador Canedo",
    "Trindade",
    "Goianira",
)

TECH_TERMS = (
    "desenvolvedor júnior",
    "programador",
    "estágio desenvolvimento",
    "estágio TI",
    "backend",
    "frontend",
    "full stack",
    "analista de dados",
    "BI",
    "ciência de dados",
    "suporte TI",
    "infraestrutura",
    "DevOps",
    "analista de sistemas",
    "QA",
    "automação",
    "inteligência artificial",
)


@dataclass(frozen=True)
class LocalDiscoveryQuerySet:
    locations: tuple[str, ...] = LOCAL_AREAS
    terms: tuple[str, ...] = TECH_TERMS

    def iter_queries(self):
        for location in self.locations:
            for term in self.terms:
                yield f'"{location}" "{term}"'
