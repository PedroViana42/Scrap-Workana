# Local Development

## Subir PostgreSQL

```bash
docker compose up -d postgres
docker compose ps
```

The development database is exposed only on `127.0.0.1:5432`.

## Configurar .env

Copy the development examples from `.env.example` into your local `.env` when needed:

```text
DATABASE_URL=postgresql+psycopg://radar:radar_dev@localhost:5432/radar
TEST_DATABASE_URL=postgresql+psycopg://radar:radar_dev@localhost:5432/radar_test
POSTGRES_DB=radar
POSTGRES_USER=radar
POSTGRES_PASSWORD=radar_dev
POSTGRES_PORT=5432
```

These are local development credentials only. If `127.0.0.1:5432` is already used, set `POSTGRES_PORT` to another local port and adjust `DATABASE_URL`/`TEST_DATABASE_URL` to match.

## Aplicar Migrations

```bash
alembic upgrade head
alembic current
alembic heads
```

## Sincronizar Sources

```bash
python -m radar.cli db-check
python -m radar.cli sync-sources
```

## Rodar Testes Unitarios

```bash
pytest -m "not integration" -q
```

## Rodar Testes De Integracao

Integration tests require `TEST_DATABASE_URL` and refuse to run unless the database name is `radar_test`.

```bash
pytest -m integration -q
```

## Resetar Ambiente Local

Stops containers while preserving the named PostgreSQL volume:

```bash
docker compose down
```

Stops containers and deletes local PostgreSQL data:

```bash
docker compose down -v
```

Use `-v` carefully: it removes the local `radar_postgres_data` volume.
