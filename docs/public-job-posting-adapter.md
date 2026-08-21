# Public JobPosting adapter pilot

This pilot reads schema.org `JobPosting` data from explicitly allowlisted public
domains. It is separate from Radar collectors and persisted `Job` records. It
does not write to PostgreSQL, run relevance scoring, or schedule recurring work.

The only configured domain is `portaldoestagio.com.br`. Discovery starts from
its public sitemap, follows only same-domain HTTPS sitemap URLs, and reads at
most 20 matching `/vaga/{numeric-id}/` pages per CLI execution. Canonical URLs
must remain on the allowlisted domain. Application URLs are retained as data
and are never fetched.

Run a controlled read-only report with:

```bash
python -m radar.cli public-job-postings \
  --domain portaldoestagio.com.br \
  --limit 20
```

The report deliberately omits complete descriptions. `Portal do Estágio` is
treated as an intermediary rather than the final employer, so the company is
left confidential unless the structured data clearly names another employer.

Public accessibility and `robots.txt` do not grant contractual permission for
recurring collection or redistribution. A separate operational and legal
decision is required before enabling persistence, scheduling, or production
use.
