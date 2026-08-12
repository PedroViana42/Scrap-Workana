# Radar Deployment

## Arquitetura CI/CD

Production deploy flows through GitHub Actions:

```text
push main
  -> tests
  -> Docker build
  -> GHCR
  -> SSH VPS
  -> pull immutable image digest
  -> migrate
  -> bootstrap
  -> scheduler
  -> verification
```

The workflow is defined in:

```text
.github/workflows/radar-production.yml
```

Deploy runs only from `refs/heads/main`.

## GitHub Environment

The production job uses the `production` environment.

Required secret names:

```text
VPS_HOST
VPS_PORT
VPS_USER
VPS_SSH_PRIVATE_KEY
VPS_KNOWN_HOSTS
```

Values must never be committed.

## GHCR

The build job publishes:

```text
ghcr.io/<github-owner-lowercase>/radar
```

The workflow uses `GITHUB_TOKEN` for GHCR push. No PAT is required for build.

For remote pull, the deploy job sends a temporary token over SSH stdin. The VPS deploy script uses a temporary `DOCKER_CONFIG`, logs into GHCR with `--password-stdin`, pulls the image, logs out, and deletes the temp config.

The package visibility is not changed automatically. If remote pull fails with 401/403, review GHCR package permissions or visibility.

## Image Tags And Digest

Each build publishes:

```text
sha-<GITHUB_SHA>
main
```

Deploy uses the immutable digest:

```text
ghcr.io/.../radar@sha256:...
```

The moving `main` tag is for convenience only.

## Deploy

The workflow transfers only:

```text
compose.prod.yaml
deploy/remote_deploy.sh
```

It does not send `.env`, database passwords, or source code. The application code comes from the GHCR image.

The VPS must already have:

```text
/opt/radar/.env
```

The deploy script validates:

- `/var/run/reboot-required` is absent;
- Docker is available;
- Compose config is valid with the new image;
- image import works before touching the scheduler.

The Compose project name is always:

```text
radar
```

## Migration

Migrations run as the `migrate` service with the new image:

```text
alembic upgrade head
```

The deploy script does not run automatic downgrades.

If migration fails, deploy fails. If a previous image exists, the script can try to restore the previous scheduler image, but database schema is not reverted.

## Bootstrap

After migration, the `bootstrap` service runs:

```text
python -m radar.cli bootstrap
```

It syncs:

- `sources`;
- `company_sources`.

It does not collect jobs.

Expected catalog:

```text
sources=13
company_sources=45
enabled_company_sources=45
```

## Scheduler

The scheduler service runs:

```text
python -m radar.cli scheduler
```

It uses:

- APScheduler;
- PostgreSQL advisory lock;
- batch processing;
- lifecycle guards.

The deploy script waits briefly and checks that the scheduler is running without startup tracebacks or restart loop.

## Metadata

The VPS stores non-secret deployment metadata:

```text
/opt/radar/deploy/current_image
/opt/radar/deploy/previous_image
/opt/radar/deploy/last_deploy_sha
/opt/radar/deploy/last_deploy_at
/opt/radar/deploy/current.env
```

`current.env` contains only:

```text
RADAR_IMAGE=<image_ref>
```

## Rollback

Rollback is image-only and best-effort.

If the new scheduler fails after the old scheduler was stopped and `previous_image` exists, the script attempts to start the scheduler with the previous image.

Rollback does not run:

```text
alembic downgrade
```

Image rollback is not database rollback.

## Troubleshooting

Host key mismatch:

- update the `VPS_KNOWN_HOSTS` secret with the trusted host key;
- do not use dynamic `ssh-keyscan` trust in the workflow.

GHCR 401/403:

- confirm the package is linked to the repository;
- confirm package visibility/permissions allow this workflow token to pull;
- do not create a PAT or make the package public automatically without review.

Migration failure:

- inspect deploy logs;
- inspect Alembic head on the VPS;
- do not downgrade automatically.

Scheduler lock:

- `scheduler_lock_unavailable` means another scheduler process holds the advisory lock;
- check `docker compose -p radar ps`;
- avoid starting a second scheduler manually.

Scheduler restart loop:

- inspect `docker logs`;
- verify `/opt/radar/.env`;
- verify `DATABASE_URL` points to `postgres` inside Docker, not `localhost`.

Reboot required:

- if `/var/run/reboot-required` exists, the workflow stops before deploy;
- reboot the VPS manually and rerun the workflow.
