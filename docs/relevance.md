# Job Relevance Engine

The relevance score ranks jobs from `0` to `100` for Radar's initial focus. It does not delete, hide, or reject jobs.

Score is deterministic and versioned. Current version:

```text
tech_early_career_br:v1.1
```

## Profile

`tech_early_career_br` prioritizes:

- internships, trainee, junior, new grad, entry-level, associate, level 1, and engineer I roles;
- Brazil, LATAM explicitly including Brazil, or globally remote opportunities;
- backend, data engineering, analytics engineering, AI/ML, automation, software engineering;
- Python, SQL, PostgreSQL, FastAPI, Airflow, Snowflake, Machine Learning, AI, LLM, Data Engineering;
- supporting stacks such as C#, .NET, Node.js, TypeScript, React, Docker, Kubernetes, AWS, Azure, GCP, Kafka, dbt, Spark.

## Dimensions

Natural total: `100`.

| Component | Max |
| --- | ---: |
| Role fit | 25 |
| Seniority fit | 25 |
| Location / eligibility | 20 |
| Technology fit | 20 |
| Freshness | 10 |

## Calibration v1.1

Version `v1.1` hardens false positives found in live smoke tests:

- title-first role detection: title evidence is stronger than description evidence;
- description-only technical terms cannot turn a non-tech title into a high-fit technical role;
- roles are classified as `TECH_EXPLICIT`, `TECH_ADJACENT`, `AMBIGUOUS`, or `NON_TECH`;
- risk, finance, compliance, AML, fraud, audit, and internal controls titles are capped, even when Python/SQL/ML appear in the description;
- security engineering exceptions remain technical: `Security Engineer`, `Cybersecurity Risk Engineer`, and `Technology Risk Engineer` are not classified as non-tech only because they contain `risk`;
- remote alone is not Brazil eligibility.

## Role Classification

`TECH_EXPLICIT` includes backend, software, data engineering, analytics engineering, AI/ML, platform/devops, QA, frontend, automation, and security engineering titles.

`TECH_ADJACENT` includes data analyst, business analyst, model risk, IT risk, solution/sales engineering, and engineering/technical management signals.

`AMBIGUOUS` means technical evidence appeared only outside the title or the title is too generic.

`NON_TECH` includes marketing, sales, recruiting, legal, finance/accounting, product/project/program management, design, financial analyst, and risk analyst titles.

## Geography

Location is normalized into categories:

| Category | Meaning |
| --- | --- |
| `BRAZIL` | Brazil or Brazilian city/state signal |
| `LATAM_INCLUDING_BRAZIL` | LATAM/Latin America without Brazil exclusion, or explicitly including Brazil |
| `GLOBAL` | Worldwide/global/anywhere remote |
| `REMOTE_UNSCOPED` | Remote, but no Brazil/LATAM/global eligibility |
| `FOREIGN_RESTRICTED` | Foreign location without Brazil eligibility, such as Colombia, Mexico, US, Canada, UK, Germany, Spain, Portugal |
| `BRAZIL_EXCLUDED` | Explicit exclusion such as LATAM excluding Brazil |

Remote US, Remote Colombia, and foreign regional/on-site jobs do not score high without Brazil, LATAM including Brazil, or global eligibility.

## Seniority

Early-career aliases include `intern`, `internship`, `trainee`, `junior`, `jr`, `entry level`, `early career`, `new grad`, `graduate`, `associate`, `level 1`, `level I`, and `engineer I`.

Mid aliases include `mid`, `mid-level`, `pleno`, `engineer II`, and `engineer III`.

High seniority aliases include `senior`, `sr`, `staff`, `principal`, `lead`, `master`, `specialist`, `manager`, `director`, `head`, and `vp`.

The experience parser recognizes contextual requirements such as `0-1`, `0-2`, `1-2`, `1+`, `2+`, `3+`, `5+`, `10+ years/anos`, while avoiding unrelated phrases like team age.

## Penalties And Caps

Some signals cap the final score:

- non-tech title: max `24`;
- tech-adjacent title: max `54`;
- ambiguous title: max `60`;
- internship/trainee calibration: max `94`;
- foreign restricted location: max `55`;
- foreign tech-adjacent role: max `49`;
- foreign staff/principal/lead role: max `39`;
- LATAM excluding Brazil: max `39`;
- staff/principal/lead-level title: max `55`;
- manager-level title: max `55`;
- director/head/VP title: max `35`;
- senior/master/specialist role: max `65`.

Salary is not part of the score in this version.

Company priority is not part of the score in this version.

## Golden Ranking

The calibration tests assert this order:

1. Junior Backend Engineer | Brazil
2. Data Engineering Internship | Brazil
3. Software Engineer I | Worldwide
4. Backend Engineer | Brazil
5. Junior Frontend | Brazil
6. Senior Backend | Brazil
7. Junior Software Engineer | Colombia
8. IT Risk Management Specialist | Brazil
9. Marketing Manager | Brazil

## Rescore

Existing jobs can be recalculated with:

```bash
python -m radar.cli rescore-jobs --dry-run
python -m radar.cli rescore-jobs
```

The command processes jobs in keyset-paginated batches and commits each batch independently.
Use `--only-outdated` to skip jobs already scored by the current engine version, and
`--batch-size` to tune the transaction size. By default it includes active and inactive jobs;
`--active-only` restricts the operation to active jobs.

Dry-run collection with score:

```bash
python -m radar.cli collect --source lever --company "CI&T" --identifier ciandt --score --limit 20
```
