# Radar Scheduler

The scheduler is a separate long-running process for collecting jobs from enabled company boards.

It does not implement API, site, Telegram, deals, LLM enrichment, Redis, Celery, or deployment concerns.

## Architecture

Runtime entrypoints:

```bash
python -m radar.cli scheduler
python -m radar.cli scheduler --once
python -m radar.cli scheduler --once --dry-run
python -m radar.cli scheduler-status
```

Package layout:

```text
radar/scheduler/
  scheduler.py
  cycle.py
  locking.py
```

The collector remains responsible only for fetching/parsing. `JobCollectionService` owns persistence, relevance scoring, `ScrapeRun`, and lifecycle decisions.

## Library

The scheduler uses APScheduler 3.x:

```text
APScheduler>=3.11,<4
```

Version 4.x pre-releases are intentionally avoided.

## Scheduling

The scheduler does not create one cron job per company.

Each tick:

1. Lists enabled `CompanySource` rows whose `Source` is also enabled.
2. Uses `source.interval_minutes` as the default interval.
3. Allows `company_sources.metadata.interval_minutes` to override the source interval.
4. Determines which boards are due.
5. Sorts by most overdue first.
6. Processes at most the configured batch size.

Defaults:

```text
RADAR_SCHEDULER_POLL_SECONDS=60
RADAR_SCHEDULER_BATCH_SIZE=5
RADAR_SCHEDULER_TIMEZONE=UTC
```

The initial active ATS intervals are:

| Source | Interval |
| --- | ---: |
| Greenhouse | 60 minutes |
| Lever | 60 minutes |
| Ashby | 60 minutes |

Concurrency is intentionally `1`: one company board at a time.

## Due Calculation

A company source is due when:

- it has never had a finished `ScrapeRun`; or
- `now >= last_finished_at + interval_minutes`.

The scheduler uses the most recent finished run, regardless of status, for cooldown. This means `FAILED` and `PARTIAL` runs also prevent the same board from being hammered every minute.

`finished_at` is preferred over `started_at` because it represents when the previous attempt actually ended.

## ScrapeRun

Migration `20260812_0003` adds:

- `scrape_runs.company_source_id`, nullable FK to `company_sources`;
- index on `scrape_runs.company_source_id`;
- index on `(company_source_id, started_at)`;
- `scrape_runs.items_deactivated`;
- `jobs.deactivated_at`.

Real company board runs fill `company_source_id`. The field remains nullable for future source-level runs.

## Lifecycle

Jobs already have:

- `active`;
- `first_seen_at`;
- `last_seen_at`;
- `company_source_id`.

Version 0003 adds:

- `deactivated_at`.

The scheduler uses a two-successful-miss rule without a `miss_count` column.

Algorithm after a full `SUCCESS` run:

1. Find the previous successful full run for the same `company_source_id`.
2. If there is no previous success, do nothing.
3. Find active jobs for that company source where `last_seen_at < previous_success.started_at`.
4. Those jobs were absent from the previous success and from the current success.
5. Set `active = false` and `deactivated_at = now`.

Only `SUCCESS` runs advance lifecycle.

`FAILED` and `PARTIAL` runs never deactivate jobs.

## Reactivation

If an inactive job reappears:

- `active = true`;
- `deactivated_at = NULL`;
- `last_seen_at` is updated;
- `first_seen_at` is preserved.

This happens through the normal job upsert path.

## Safety Guards

Two guards prevent destructive lifecycle changes on suspicious responses:

### Suspicious Empty Result

If a board had active jobs before collection and returns `0 jobs`, the run becomes:

```text
PARTIAL / SuspiciousEmptyResult
```

Jobs found are still persisted when present, but a zero response does not deactivate existing jobs.

### Suspicious Result Drop

If:

```text
active_before >= 10
items_found < active_before * RADAR_LIFECYCLE_MIN_RESULT_RATIO
```

the run becomes:

```text
PARTIAL / SuspiciousResultDrop
```

Default:

```text
RADAR_LIFECYCLE_MIN_RESULT_RATIO=0.20
```

`PARTIAL` does not advance lifecycle.

## Singleton Lock

The continuous scheduler uses PostgreSQL advisory lock:

```text
pg_try_advisory_lock(...)
```

`RadarSchedulerLock` keeps a dedicated connection open for the life of the process. If another scheduler already holds the lock, the second process exits instead of collecting duplicate data.

When the process exits or the connection dies, PostgreSQL releases the lock.

## Graceful Shutdown

The scheduler handles:

- `SIGINT`;
- `SIGTERM`.

On shutdown it:

- stops accepting new cycles;
- shuts down APScheduler;
- releases the advisory lock;
- disposes database connections.

## CLI

Continuous mode:

```bash
python -m radar.cli scheduler
```

Single cycle:

```bash
python -m radar.cli scheduler --once
```

Dry-run, no HTTP and no writes:

```bash
python -m radar.cli scheduler --once --dry-run
```

Limit companies for controlled runs:

```bash
python -m radar.cli scheduler --once --max-companies 3
```

Status:

```bash
python -m radar.cli scheduler-status
```

Status prints:

- enabled company sources;
- due now;
- last success;
- run counts by status in the last 24 hours.
