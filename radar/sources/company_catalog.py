from radar.sources.models import CompanySource


def get_company_catalog(source_name: str | None = None) -> list[CompanySource]:
    companies = (
        _greenhouse_companies()
        + _lever_companies()
        + _ashby_companies()
        + _workable_companies()
        + _smartrecruiters_companies()
    )
    if source_name is None:
        return companies
    normalized = source_name.lower().strip()
    return [company for company in companies if company.source_name == normalized]


def _company(
    company_name: str,
    source_name: str,
    external_identifier: str,
    country: str | None,
    tags: tuple[str, ...],
    priority: int,
    metadata: dict | None = None,
) -> CompanySource:
    return CompanySource(
        company_name=company_name,
        source_name=source_name,
        external_identifier=external_identifier,
        enabled=True,
        country=country,
        tags=tags,
        metadata={"priority": priority, **(metadata or {})},
    )


def _greenhouse_companies() -> list[CompanySource]:
    return [
        _company("Airbnb", "greenhouse", "airbnb", None, ("engineering", "data", "backend", "remote"), 80),
        _company("Wellhub / Gympass", "greenhouse", "gympass", "BR", ("brazil", "latam", "engineering", "backend", "data", "remote"), 100),
        _company("Wildlife Studios", "greenhouse", "wildlifestudios", "BR", ("brazil", "engineering", "backend", "data", "ai", "ml"), 100),
        _company("Launch Potato", "greenhouse", "launchpotato", None, ("latam", "remote", "engineering", "data"), 80),
        _company("ClickHouse", "greenhouse", "clickhouse", None, ("remote", "engineering", "backend", "data", "database", "cloud"), 80),
        _company("Cision", "greenhouse", "cision", None, ("engineering", "data", "platform"), 60),
        _company("Figma", "greenhouse", "figma", None, ("engineering", "frontend", "backend", "data", "ai"), 80),
        _company("Kaizen Gaming", "greenhouse", "kaizengaming", None, ("engineering", "backend", "data", "qa"), 60),
        _company("Nearform", "greenhouse", "nearform", None, ("remote", "engineering", "backend", "frontend", "cloud"), 80),
        _company("Goodway Group", "greenhouse", "goodwaygroup", None, ("remote", "engineering", "data"), 60),
        _company("Speechify", "greenhouse", "speechify", None, ("remote", "engineering", "ai", "ml", "backend"), 80),
        _company("Cloudflare", "greenhouse", "cloudflare", None, ("engineering", "backend", "security", "cloud", "platform"), 80),
        _company("Datadog", "greenhouse", "datadog", None, ("engineering", "devops", "cloud", "platform", "data"), 80),
        _company("MongoDB", "greenhouse", "mongodb", None, ("engineering", "backend", "data", "database", "cloud"), 80),
        _company("Elastic", "greenhouse", "elastic", None, ("remote", "engineering", "data", "security", "cloud"), 80),
        _company("Stripe", "greenhouse", "stripe", None, ("engineering", "backend", "data", "security", "platform"), 80),
        _company("Canonical", "greenhouse", "canonical", None, ("remote", "engineering", "devops", "cloud", "platform"), 80),
    ]


def _lever_companies() -> list[CompanySource]:
    return [
        _company("CI&T", "lever", "ciandt", "BR", ("brazil", "latam", "engineering", "backend", "frontend", "data", "qa"), 100),
        _company("Oowlish", "lever", "oowlish", None, ("latam", "remote", "engineering", "backend", "frontend", "data"), 100),
        _company("Swile", "lever", "swile", None, ("engineering", "backend", "data"), 60),
        _company("Yuno", "lever", "yuno", None, ("latam", "remote", "engineering", "backend", "data"), 100),
        _company("Spotify", "lever", "spotify", None, ("engineering", "backend", "data", "platform", "early-career"), 80),
        _company("Binance", "lever", "binance", None, ("remote", "engineering", "backend", "data", "security", "devops"), 80),
        _company("Aircall", "lever", "aircall", None, ("engineering", "backend", "frontend", "data"), 60),
        _company("Coupa", "lever", "coupa", None, ("engineering", "backend", "data", "cloud"), 60),
        _company("Shield AI", "lever", "shieldai", None, ("engineering", "ai", "ml", "devops", "platform"), 80),
        _company("Lyra Health", "lever", "lyrahealth", None, ("engineering", "data", "backend", "platform"), 60),
    ]


def _ashby_companies() -> list[CompanySource]:
    return [
        _company("Nubank", "ashby", "nubank", "BR", ("brazil", "latam", "engineering", "backend", "data", "ai", "ml"), 100),
        _company("Canals", "ashby", "canals", None, ("engineering", "backend", "data", "ai"), 80),
        _company("Camunda", "ashby", "camunda", None, ("remote", "engineering", "backend", "cloud", "platform"), 80),
        _company("Pyyne", "ashby", "pyyne", "BR", ("brazil", "engineering", "data"), 80),
        _company("Articul8 AI", "ashby", "articul8", None, ("ai", "ml", "engineering", "data", "platform"), 80),
        _company("Sardine", "ashby", "sardine", None, ("remote", "engineering", "backend", "data", "security"), 80),
        _company("Alternative Payments", "ashby", "alternativepayments", None, ("engineering", "backend", "data"), 60),
        _company("Skydropx / Frenet", "ashby", "skydropx", None, ("latam", "engineering", "backend", "data"), 80),
        _company("Tako", "ashby", "tako", None, ("engineering", "ai", "data"), 80),
        _company("Tempo", "ashby", "tempo", None, ("engineering", "backend", "data"), 60),
        _company("Oscilar", "ashby", "oscilar", None, ("brazil", "engineering", "data", "ai", "ml"), 80),
        _company("LiteLLM", "ashby", "litellm", None, ("remote", "engineering", "ai", "ml", "backend"), 80),
        _company("Jump", "ashby", "jump", None, ("engineering", "ai", "ml"), 60),
        _company("Feegow", "ashby", "feegow", "BR", ("brazil", "engineering", "healthtech"), 60),
        _company("ElevenLabs", "ashby", "elevenlabs", None, ("remote", "engineering", "ai", "ml", "backend"), 80),
        _company("LangChain", "ashby", "langchain", None, ("remote", "engineering", "ai", "ml", "backend"), 80),
        _company("Supabase", "ashby", "supabase", None, ("remote", "engineering", "backend", "database", "cloud"), 80),
        _company("Docker", "ashby", "docker", None, ("remote", "engineering", "devops", "cloud", "platform"), 80),
    ]


def _workable_companies() -> list[CompanySource]:
    return [
        _company(
            "Tenchi Security",
            "workable",
            "tenchi-security",
            "BR",
            ("brazil", "remote", "engineering", "backend", "security", "early-career"),
            100,
        ),
        _company(
            "GigaBrands",
            "workable",
            "gigabrands",
            None,
            ("brazil", "latam", "remote", "engineering", "ai"),
            80,
        ),
        _company(
            "WATI",
            "workable",
            "wati-dot-i-o",
            None,
            ("brazil", "latam", "remote", "engineering", "backend", "ai"),
            80,
        ),
    ]


def _smartrecruiters_companies() -> list[CompanySource]:
    collection = {
        "country_filter": "br",
        "reconciliation_interval_hours": 24,
        "incremental_overlap_minutes": 5,
    }
    return [
        _company(
            "Experian",
            "smartrecruiters",
            "Experian",
            "BR",
            ("brazil", "remote", "engineering", "backend", "data", "early-career"),
            100,
            collection,
        ),
        _company(
            "Bosch Group",
            "smartrecruiters",
            "BoschGroup",
            "BR",
            ("brazil", "engineering", "data", "early-career"),
            80,
            collection,
        ),
        _company(
            "MSX International",
            "smartrecruiters",
            "MSXInternational",
            "BR",
            ("brazil", "remote", "engineering", "data"),
            60,
            collection,
        ),
    ]
