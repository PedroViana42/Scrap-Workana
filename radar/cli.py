import argparse
import logging
from pathlib import Path

from sqlalchemy import text
from radar.database.repositories.sources import SourceRepository, sync_source_catalog
from radar.database.repositories.company_sources import CompanySourceRepository, sync_company_catalog
from radar.database.session import session_scope
from radar.logging_config import configure_logging
from radar.services.job_collection import JobCollectionService, company_source_db_to_domain
from radar.services.company_validation import validate_company_catalog
from radar.database.repositories.jobs import JobRepository
from radar.models.enums import EmploymentType, RemoteType, Seniority
from radar.models.job import Job
from radar.relevance.profiles import TECH_EARLY_CAREER_BR_PROFILE
from radar.relevance.scoring import score_job
from radar.scheduler.cycle import run_scheduler_cycle, list_due_company_sources, scheduler_batch_size
from radar.scheduler.scheduler import RadarScheduler
from radar.sources.models import CompanySource
from radar.sources.types import ContentType


logger = logging.getLogger(__name__)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def db_check() -> int:
    with session_scope() as session:
        result = session.execute(text("SELECT 1")).scalar_one()
    print(f"db-check ok: {result}")
    return 0


def sync_sources() -> int:
    with session_scope() as session:
        synced = sync_source_catalog(session)
        repository = SourceRepository(session)
        enabled_count = len(repository.list_enabled())
        job_count = sum(1 for source in synced if source.content_type == ContentType.JOB.value)
        deal_count = sum(1 for source in synced if source.content_type == ContentType.DEAL.value)

    print(
        "sync-sources ok: "
        f"{len(synced)} sources, {job_count} job, {deal_count} deal, {enabled_count} enabled"
    )
    return 0


def sync_companies() -> int:
    with session_scope() as session:
        sync_source_catalog(session)
        synced = sync_company_catalog(session)
        by_source: dict[str, int] = {}
        for company_source in synced:
            by_source[company_source.source.name] = by_source.get(company_source.source.name, 0) + 1
    print(
        "sync-companies ok: "
        f"{len(synced)} companies, "
        + ", ".join(f"{source}={count}" for source, count in sorted(by_source.items()))
    )
    return 0


def bootstrap() -> int:
    with session_scope() as session:
        sources = sync_source_catalog(session)
        companies = sync_company_catalog(session)
        enabled_companies = sum(1 for company_source in companies if company_source.enabled)
    print(
        "bootstrap ok: "
        f"sources={len(sources)}, company_sources={len(companies)}, "
        f"enabled_company_sources={enabled_companies}"
    )
    return 0


def validate_companies(args: argparse.Namespace) -> int:
    results = validate_company_catalog(args.source)
    valid_count = 0
    invalid_count = 0
    requests_by_source: dict[str, int] = {}

    for result in results:
        company = result.company_source
        requests_by_source[company.source_name] = requests_by_source.get(company.source_name, 0) + result.requests
        if result.valid:
            valid_count += 1
            print(
                f"[OK] {company.source_name} / {company.company_name} / "
                f"{company.external_identifier} / {result.jobs_count} jobs"
            )
        else:
            invalid_count += 1
            print(
                f"[FAIL] {company.source_name} / {company.company_name} / "
                f"{company.external_identifier} / {result.error}"
            )

    print(f"Boards consultados: {len(results)}")
    print(f"Válidos: {valid_count}")
    print(f"Inválidos: {invalid_count}")
    print(f"Requests: {sum(requests_by_source.values())}")
    for source_name, count in sorted(requests_by_source.items()):
        print(f"{source_name}: {count}")
    return 0 if invalid_count == 0 else 1


def collect(args: argparse.Namespace) -> int:
    if args.company_source_id is not None:
        with session_scope() as session:
            company_source_db = CompanySourceRepository(session).get_by_id(args.company_source_id)
            if company_source_db is None:
                raise SystemExit(f"CompanySource not found: {args.company_source_id}")
            company_source = company_source_db_to_domain(company_source_db)
            if args.persist:
                summary = JobCollectionService(session).collect_and_persist(company_source)
                _print_persist_summary(summary)
                return 0
        return _dry_run(company_source, score=args.score, limit=args.limit)

    if not args.source or not args.company or not args.identifier:
        raise SystemExit("Use --company-source-id or provide --source, --company, and --identifier")

    company_source = CompanySource(
        company_name=args.company,
        source_name=args.source,
        external_identifier=args.identifier,
        metadata={"api_region": args.api_region} if args.api_region else {},
    )

    if args.persist:
        with session_scope() as session:
            summary = JobCollectionService(session).collect_and_persist(
                company_source,
                persist_company_source=args.save_company_source,
            )
            _print_persist_summary(summary)
        return 0

    return _dry_run(company_source, score=args.score, limit=args.limit)


def _dry_run(company_source: CompanySource, score: bool = False, limit: int = 5) -> int:
    from radar.collectors.registry import default_registry

    collector_cls = default_registry.get(company_source.source_name)
    collector = collector_cls(company_source=company_source)
    collected = collector.collect()
    print(f"Source: {collected.source_name}")
    print(f"Company: {company_source.company_name}")
    print(f"Jobs encontrados: {collected.items_found}")
    if score:
        scored = [(score_job(collected_job.job), collected_job.job) for collected_job in collected.jobs]
        scored.sort(key=lambda item: item[0].score, reverse=True)
        print("Top vagas por score:")
        for relevance, job in scored[:limit]:
            print(f"{relevance.score:3d}  {job.title} | {job.location or 'N/A'}")
    else:
        print("Primeiras vagas:")
        for collected_job in collected.jobs[:limit]:
            print(f"* {collected_job.job.title}")
    return 0


def _print_persist_summary(summary) -> None:
    print(
        "collect ok: "
        f"source={summary.source_name}, company={summary.company_name}, "
        f"found={summary.items_found}, new={summary.items_new}, updated={summary.items_updated}, "
        f"deactivated={summary.items_deactivated}, "
        f"status={summary.status.value}, scrape_run_id={summary.scrape_run_id}"
    )


def scheduler_command(args: argparse.Namespace) -> int:
    if not args.once:
        return RadarScheduler().start()

    with session_scope() as session:
        result = run_scheduler_cycle(
            session,
            dry_run=args.dry_run,
            max_companies=args.max_companies,
            batch_size=scheduler_batch_size(),
        )
        if args.dry_run:
            print(f"Due: {result.due_count}")
            for index, due_item in enumerate(result.due or [], 1):
                company_source = due_item.company_source
                print(f"{index} {company_source.source.name} / {company_source.company_name}")
            print(f"Would process: {result.would_process}")
        else:
            print(f"Due: {result.due_count}")
            print(f"Processed: {len(result.processed)}")
            for summary in result.processed:
                print(
                    f"{summary.status.value} / {summary.source_name} / {summary.company_name} / "
                    f"found={summary.items_found}, new={summary.items_new}, updated={summary.items_updated}, "
                    f"deactivated={summary.items_deactivated}"
                )
    return 0


def scheduler_status() -> int:
    with session_scope() as session:
        enabled_count = int(
            session.scalar(
                text(
                    """
                    SELECT count(*)
                    FROM company_sources cs
                    JOIN sources s ON s.id = cs.source_id
                    WHERE cs.enabled = true AND s.enabled = true
                    """
                )
            )
            or 0
        )
        due = list_due_company_sources(session)
        rows = session.execute(
            text(
                """
                SELECT status, count(*)
                FROM scrape_runs
                WHERE started_at >= now() - interval '24 hours'
                GROUP BY status
                ORDER BY status
                """
            )
        ).all()
        last_success = session.scalar(
            text("SELECT max(finished_at) FROM scrape_runs WHERE status = 'success'")
        )
    print(f"Enabled company sources: {enabled_count}")
    print(f"Due now: {len(due)}")
    print(f"Last success: {last_success or 'N/A'}")
    print("Runs last 24h:")
    if rows:
        for status, count in rows:
            print(f"  {status.upper()}: {count}")
    else:
        print("  none")
    return 0


def api_command() -> int:
    import uvicorn

    from radar.config import settings

    uvicorn.run("radar.api.app:app", host=settings.api_host, port=settings.api_port)
    return 0


def discover_local(args: argparse.Namespace) -> int:
    from radar.discovery.reporting import print_report, resolve_file

    report = resolve_file(args.input)
    print_report(report)
    return 0


def rescore_jobs(args: argparse.Namespace) -> int:
    processed = 0
    after_id = 0
    target_version = TECH_EARLY_CAREER_BR_PROFILE.version
    while args.limit is None or processed < args.limit:
        remaining = args.limit - processed if args.limit is not None else args.batch_size
        batch_limit = min(args.batch_size, remaining)
        with session_scope() as session:
            repository = JobRepository(session)
            jobs = repository.list_for_rescore(
                after_id=after_id,
                limit=batch_limit,
                exclude_version=target_version if args.only_outdated else None,
                active_only=args.active_only,
            )
            if not jobs:
                break
            for job_db in jobs:
                job = _job_db_to_domain(job_db)
                relevance = score_job(job)
                processed += 1
                if not args.dry_run:
                    repository.update_relevance(job_db.id, relevance, technologies=job.technologies)
            after_id = jobs[-1].id
            if args.dry_run:
                session.rollback()
        print(
            f"rescore-jobs progress: processed={processed}, last_id={after_id}, "
            f"dry_run={args.dry_run}"
        )
    print(
        f"rescore-jobs ok: processed={processed}, dry_run={args.dry_run}, "
        f"target_version={target_version}"
    )
    return 0


def _job_db_to_domain(job_db) -> Job:
    return Job(
        source=job_db.source.name,
        external_id=job_db.external_id,
        title=job_db.title,
        company=job_db.company,
        description=job_db.description,
        url=job_db.url,
        location=job_db.location,
        remote_type=RemoteType(job_db.remote_type),
        employment_type=EmploymentType(job_db.employment_type),
        seniority=Seniority(job_db.seniority),
        salary_min=job_db.salary_min,
        salary_max=job_db.salary_max,
        salary_currency=job_db.salary_currency,
        technologies=list(job_db.technologies or []),
        published_at=job_db.published_at,
        collected_at=job_db.collected_at,
        metadata=job_db.metadata_,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m radar.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("db-check")
    subparsers.add_parser("bootstrap")
    subparsers.add_parser("sync-sources")
    subparsers.add_parser("sync-companies")
    validate_parser = subparsers.add_parser("validate-companies")
    collector_sources = ["greenhouse", "lever", "ashby", "workable", "smartrecruiters"]
    validate_parser.add_argument("--source", choices=collector_sources)
    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--source", choices=collector_sources)
    collect_parser.add_argument("--company")
    collect_parser.add_argument("--identifier")
    collect_parser.add_argument("--company-source-id", type=int)
    collect_parser.add_argument("--api-region", choices=["global", "eu"])
    collect_parser.add_argument("--persist", action="store_true")
    collect_parser.add_argument("--save-company-source", action="store_true")
    collect_parser.add_argument("--score", action="store_true")
    collect_parser.add_argument("--limit", type=int, default=5)
    rescore_parser = subparsers.add_parser("rescore-jobs")
    rescore_parser.add_argument("--dry-run", action="store_true")
    rescore_parser.add_argument("--limit", type=positive_int)
    rescore_parser.add_argument("--batch-size", type=positive_int, default=500)
    rescore_parser.add_argument("--only-outdated", action="store_true")
    rescore_parser.add_argument("--active-only", action="store_true")
    scheduler_parser = subparsers.add_parser("scheduler")
    scheduler_parser.add_argument("--once", action="store_true")
    scheduler_parser.add_argument("--dry-run", action="store_true")
    scheduler_parser.add_argument("--max-companies", type=int)
    subparsers.add_parser("scheduler-status")
    subparsers.add_parser("api")
    discovery_parser = subparsers.add_parser(
        "discover-local",
        help="Resolve supplied public discovery results without persistence or network access",
    )
    discovery_parser.add_argument("--input", required=True, type=Path)
    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "db-check":
        return db_check()
    if args.command == "bootstrap":
        return bootstrap()
    if args.command == "sync-sources":
        return sync_sources()
    if args.command == "sync-companies":
        return sync_companies()
    if args.command == "validate-companies":
        return validate_companies(args)
    if args.command == "collect":
        return collect(args)
    if args.command == "rescore-jobs":
        return rescore_jobs(args)
    if args.command == "scheduler":
        return scheduler_command(args)
    if args.command == "scheduler-status":
        return scheduler_status()
    if args.command == "api":
        return api_command()
    if args.command == "discover-local":
        return discover_local(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
