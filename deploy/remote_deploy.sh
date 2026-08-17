#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE_REF="${1:?IMAGE_REF is required}"
WEB_IMAGE_REF="${2:?WEB_IMAGE_REF is required}"
GHCR_USER="${3:?GHCR_USER is required}"
DEPLOY_SHA="${4:?DEPLOY_SHA is required}"

IFS= read -r GHCR_TOKEN

BASE_DIR="/opt/radar"
DEPLOY_DIR="$BASE_DIR/deploy"
ENV_FILE="$BASE_DIR/.env"
NEW_COMPOSE="$DEPLOY_DIR/compose.prod.yaml.new"
FINAL_COMPOSE="$BASE_DIR/compose.prod.yaml"
NEW_SCRIPT="$DEPLOY_DIR/remote_deploy.sh.new"
FINAL_SCRIPT="$DEPLOY_DIR/remote_deploy.sh"
LOCK_FILE="$DEPLOY_DIR/deploy.lock"
CURRENT_IMAGE_FILE="$DEPLOY_DIR/current_image"
PREVIOUS_IMAGE_FILE="$DEPLOY_DIR/previous_image"
CURRENT_WEB_IMAGE_FILE="$DEPLOY_DIR/current_web_image"
PREVIOUS_WEB_IMAGE_FILE="$DEPLOY_DIR/previous_web_image"
LAST_DEPLOY_SHA_FILE="$DEPLOY_DIR/last_deploy_sha"
LAST_DEPLOY_AT_FILE="$DEPLOY_DIR/last_deploy_at"
CURRENT_ENV_FILE="$DEPLOY_DIR/current.env"
DOCKER_CONFIG_DIR=""
PREVIOUS_IMAGE=""
PREVIOUS_WEB_IMAGE=""
SCHEDULER_WAS_STOPPED=0

log() {
  printf '[radar-deploy] %s\n' "$*"
}

fail() {
  log "$*"
  rollback_image_best_effort
  exit 1
}

cleanup() {
  if [[ -n "$DOCKER_CONFIG_DIR" && -d "$DOCKER_CONFIG_DIR" ]]; then
    docker --config "$DOCKER_CONFIG_DIR" logout ghcr.io >/dev/null 2>&1 || true
    rm -rf "$DOCKER_CONFIG_DIR"
  fi
}

rollback_image_best_effort() {
  if [[ -z "$PREVIOUS_IMAGE" || "$SCHEDULER_WAS_STOPPED" != "1" ]]; then
    log "No previous scheduler image rollback attempted."
    return
  fi

  log "Attempting best-effort image rollback. Database migrations are not reverted."
  if [[ -f "$FINAL_COMPOSE" && -f "$ENV_FILE" ]]; then
    RADAR_IMAGE="$PREVIOUS_IMAGE" \
      RADAR_WEB_IMAGE="${PREVIOUS_WEB_IMAGE:-$WEB_IMAGE_REF}" \
      docker compose \
      -p radar \
      --env-file "$ENV_FILE" \
      -f "$FINAL_COMPOSE" \
      up -d scheduler api web || log "Best-effort rollback failed."
  fi
}

on_error() {
  log "Deploy failed."
  rollback_image_best_effort
}

trap cleanup EXIT
trap on_error ERR

mkdir -p "$DEPLOY_DIR"
exec 9>"$LOCK_FILE"
if ! flock -w 300 9; then
  log "Another deploy is already running."
  exit 1
fi

if [[ -f /var/run/reboot-required ]]; then
  log "VPS requires reboot before first Radar deployment."
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  log "/opt/radar/.env is missing."
  exit 1
fi

if [[ ! -f "$NEW_COMPOSE" ]]; then
  log "New compose file was not uploaded: $NEW_COMPOSE"
  exit 1
fi

log "Deploy SHA: $DEPLOY_SHA"
log "Image: $IMAGE_REF"
log "Web image: $WEB_IMAGE_REF"

DOCKER_CONFIG_DIR="$(mktemp -d)"
printf '%s\n' "$GHCR_TOKEN" | docker --config "$DOCKER_CONFIG_DIR" login ghcr.io -u "$GHCR_USER" --password-stdin >/dev/null

if ! docker --config "$DOCKER_CONFIG_DIR" pull "$IMAGE_REF"; then
  log "GHCR remote pull denied. Package permissions/visibility need review."
  exit 1
fi

if ! docker --config "$DOCKER_CONFIG_DIR" pull "$WEB_IMAGE_REF"; then
  log "GHCR web image pull denied. Package permissions/visibility need review."
  exit 1
fi

docker run --rm "$IMAGE_REF" python -c "import radar.cli; print('radar-image-ok')"
docker run --rm "$WEB_IMAGE_REF" node --version

RADAR_IMAGE="$IMAGE_REF" RADAR_WEB_IMAGE="$WEB_IMAGE_REF" docker compose \
  -p radar \
  --env-file "$ENV_FILE" \
  -f "$NEW_COMPOSE" \
  config >/dev/null

if [[ -f "$CURRENT_IMAGE_FILE" ]]; then
  PREVIOUS_IMAGE="$(<"$CURRENT_IMAGE_FILE")"
  printf '%s\n' "$PREVIOUS_IMAGE" > "$PREVIOUS_IMAGE_FILE"
fi
if [[ -f "$CURRENT_WEB_IMAGE_FILE" ]]; then
  PREVIOUS_WEB_IMAGE="$(<"$CURRENT_WEB_IMAGE_FILE")"
  printf '%s\n' "$PREVIOUS_WEB_IMAGE" > "$PREVIOUS_WEB_IMAGE_FILE"
fi

mv "$NEW_COMPOSE" "$FINAL_COMPOSE"
if [[ -f "$NEW_SCRIPT" ]]; then
  chmod 755 "$NEW_SCRIPT"
  mv "$NEW_SCRIPT" "$FINAL_SCRIPT"
fi

compose() {
  RADAR_IMAGE="$IMAGE_REF" RADAR_WEB_IMAGE="$WEB_IMAGE_REF" docker compose \
    -p radar \
    --env-file "$ENV_FILE" \
    -f "$FINAL_COMPOSE" \
    "$@"
}

log "Starting postgres."
compose up -d postgres

log "Stopping existing web and API, if present."
compose stop -t 30 web api

log "Stopping existing scheduler, if present."
if [[ -n "$(compose ps -q scheduler)" ]]; then
  SCHEDULER_WAS_STOPPED=1
  compose stop -t 60 scheduler
fi

log "Running migrations."
compose run --rm migrate

MIGRATION_HEAD="$(compose run --rm -T scheduler python - <<'PY'
from sqlalchemy import text
from radar.database.session import session_scope
with session_scope() as session:
    print(session.execute(text("select version_num from alembic_version")).scalar_one())
PY
)"
log "Migration head: $MIGRATION_HEAD"

log "Running bootstrap."
compose run --rm bootstrap

log "Starting scheduler."
compose up -d scheduler

log "Starting API and web."
compose up -d --wait --wait-timeout 180 api web

sleep 20

SCHEDULER_ID="$(compose ps -q scheduler)"
if [[ -z "$SCHEDULER_ID" ]]; then
  fail "Scheduler container was not created."
fi

if [[ "$(docker inspect -f '{{.State.Running}}' "$SCHEDULER_ID")" != "true" ]]; then
  fail "Scheduler container is not running."
fi

RESTART_COUNT="$(docker inspect -f '{{.RestartCount}}' "$SCHEDULER_ID")"
if [[ "$RESTART_COUNT" != "0" ]]; then
  fail "Scheduler restart loop detected: restart_count=$RESTART_COUNT"
fi

if docker logs "$SCHEDULER_ID" --since 2m 2>&1 | grep -E "Traceback|scheduler_lock_unavailable"; then
  fail "Scheduler startup logs contain an error."
fi

compose exec -T scheduler python -m radar.cli db-check
compose exec -T scheduler python -m radar.cli scheduler-status
compose exec -T api python -m radar.cli db-check

compose exec -T scheduler python - <<'PY'
from sqlalchemy import text
from radar.database.session import session_scope
with session_scope() as session:
    rows = session.execute(text("""
        select 'sources=' || count(*) from sources
        union all select 'company_sources=' || count(*) from company_sources
        union all select 'enabled_company_sources=' || count(*) from company_sources where enabled = true
        union all select 'jobs=' || count(*) from jobs
        union all select 'scored=' || count(*) from jobs where relevance_score is not null
        union all select 'v11=' || count(*) from jobs where relevance_version = 'tech_early_career_br:v1.1'
    """)).scalars()
    for row in rows:
        print(row)
PY

printf '%s\n' "$IMAGE_REF" > "$CURRENT_IMAGE_FILE"
printf '%s\n' "$WEB_IMAGE_REF" > "$CURRENT_WEB_IMAGE_FILE"
printf '%s\n' "$DEPLOY_SHA" > "$LAST_DEPLOY_SHA_FILE"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$LAST_DEPLOY_AT_FILE"
printf 'RADAR_IMAGE=%s\nRADAR_WEB_IMAGE=%s\n' "$IMAGE_REF" "$WEB_IMAGE_REF" > "$CURRENT_ENV_FILE"
chmod 644 "$CURRENT_IMAGE_FILE" "$CURRENT_WEB_IMAGE_FILE" "$LAST_DEPLOY_SHA_FILE" "$LAST_DEPLOY_AT_FILE" "$CURRENT_ENV_FILE"
if [[ -f "$PREVIOUS_IMAGE_FILE" ]]; then
  chmod 644 "$PREVIOUS_IMAGE_FILE"
fi
if [[ -f "$PREVIOUS_WEB_IMAGE_FILE" ]]; then
  chmod 644 "$PREVIOUS_WEB_IMAGE_FILE"
fi

compose ps
docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}' || true
docker system df || true

log "Deploy completed."
