# Radar Sources

Radar separates external data sources from the collectors that know how to read them.

Radar does not collect freelance projects or one-off gig marketplaces. The JOB domain is for traditional employment opportunities: internships, trainee programs, junior to senior roles, contract positions when they behave like employment, and remote, national, or international tech roles.

## Jobs

Planned job sources:

- Greenhouse
- Lever
- Ashby
- Remote OK
- We Work Remotely
- Remotive
- Gupy
- ProgramaThor
- SmartRecruiters

## Deals

Planned deal sources:

- Mercado Livre
- Amazon
- KaBuM!
- Pichau

## Concepts

`Source` describes an external source: name, display name, content type, status, optional collector name, operational requirements, priority, and capabilities.

`CompanySource` describes a monitored company board inside an ATS-style source. The `external_identifier` field is intentionally generic because each ATS uses a different board identifier.

`Collector` is the implementation that collects opportunities from a source. A source can be configured before a collector exists.

`Registry` maps source names to collector classes. It avoids source-specific `if` chains and makes future collectors pluggable.

No unconfirmed endpoints, credentials, or company identifiers are documented here.
