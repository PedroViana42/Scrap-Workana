from dataclasses import dataclass, field


SCORING_VERSION = "tech_early_career_br:v1.3"


@dataclass(frozen=True)
class JobRelevanceProfile:
    name: str
    version: str
    role_max: int = 25
    seniority_max: int = 25
    location_max: int = 20
    technology_max: int = 20
    freshness_max: int = 10
    high_priority_technologies: dict[str, int] = field(default_factory=dict)
    good_technologies: dict[str, int] = field(default_factory=dict)
    complementary_technologies: dict[str, int] = field(default_factory=dict)


TECH_EARLY_CAREER_BR_PROFILE = JobRelevanceProfile(
    name="tech_early_career_br",
    version=SCORING_VERSION,
    high_priority_technologies={
        "Python": 10,
        "SQL": 8,
        "PostgreSQL": 8,
        "FastAPI": 8,
        "Airflow": 8,
        "Snowflake": 8,
        "Machine Learning": 10,
        "LLM": 10,
        "AI": 8,
        "Data Engineering": 10,
    },
    good_technologies={
        "C#": 6,
        ".NET": 6,
        "Node.js": 6,
        "TypeScript": 6,
        "JavaScript": 5,
        "NestJS": 6,
        "React": 5,
        "Next.js": 5,
        "Docker": 5,
        "Git": 4,
        "REST API": 5,
    },
    complementary_technologies={
        "Kubernetes": 4,
        "AWS": 4,
        "Azure": 4,
        "GCP": 4,
        "Redis": 3,
        "Kafka": 4,
        "dbt": 4,
        "Spark": 4,
    },
)
