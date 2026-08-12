# Job Collectors

Radar collectors use public HTTP APIs only. They do not use Selenium, Playwright, headless browsers, proxies, login sessions, or user cookies.

Collectors only read public job announcements. Radar does not apply to jobs automatically; candidates should always use the original job URL.

## Greenhouse

`CompanySource.external_identifier` is the Greenhouse board token.

Endpoint:

```text
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
```

Dry-run:

```bash
python -m radar.cli collect --source greenhouse --company "Company" --identifier board_token
```

Persist explicitly:

```bash
python -m radar.cli collect --source greenhouse --company "Company" --identifier board_token --persist --save-company-source
```

## Lever

`CompanySource.external_identifier` is the Lever site.

Endpoint:

```text
GET https://api.lever.co/v0/postings/{site}?mode=json
```

For future EU boards, pass:

```bash
python -m radar.cli collect --source lever --company "Company" --identifier site --api-region eu
```

## Ashby

`CompanySource.external_identifier` is the Ashby job board name.

Endpoint:

```text
GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}?includeCompensation=true
```

When Ashby does not provide a stable public job ID, Radar derives a deterministic external identity from the public job URL and title.

## Persistence

The persistence flow is:

```text
CompanySource -> Collector -> Job -> JobRepository.upsert -> ScrapeRun
```

Dry-run mode performs HTTP collection and parsing but does not write jobs or company sources.

