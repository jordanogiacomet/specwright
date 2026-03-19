#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.local}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

BACKUP_FILE="${1:-${BACKUP_FILE:-}}"
EXECUTION_MODE="${RESTORE_MODE:-${POSTGRES_EXECUTION_MODE:-auto}}"
DOCKER_POSTGRES_SERVICE="${DOCKER_POSTGRES_SERVICE:-postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
RESTORE_DATABASE="${RESTORE_DATABASE:-${POSTGRES_DB:-}}"
RESTORE_DATABASE_URL="${RESTORE_DATABASE_URL:-${DATABASE_URL:-}}"
RESTORE_ADMIN_DATABASE="${RESTORE_ADMIN_DATABASE:-postgres}"
RESTORE_RECREATE_DATABASE="${RESTORE_RECREATE_DATABASE:-0}"

die() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage: bash scripts/restore.sh <backup-file>

Environment overrides:
  RESTORE_MODE=auto|host|docker
  RESTORE_DATABASE=<database name>
  RESTORE_DATABASE_URL=<postgres connection string>
  RESTORE_RECREATE_DATABASE=0|1
  RESTORE_ADMIN_DATABASE=<database used for DROP/CREATE, defaults to postgres>
  DOCKER_POSTGRES_SERVICE=<compose service name>
EOF
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

has_docker_compose() {
  command_exists docker && docker compose version >/dev/null 2>&1
}

resolve_mode() {
  case "$EXECUTION_MODE" in
    auto)
      if command_exists pg_restore; then
        printf 'host\n'
        return
      fi

      if has_docker_compose; then
        printf 'docker\n'
        return
      fi

      die "pg_restore is not installed and docker compose is unavailable. Install PostgreSQL client tools or run through Docker Compose."
      ;;
    host | docker)
      printf '%s\n' "$EXECUTION_MODE"
      ;;
    *)
      die "RESTORE_MODE must be one of: auto, host, docker."
      ;;
  esac
}

run_host_recreate_database() {
  if ! command_exists psql; then
    die "psql is required when RESTORE_RECREATE_DATABASE=1 in host mode."
  fi

  : "${POSTGRES_USER:?Missing POSTGRES_USER for host restore}"
  : "${RESTORE_DATABASE:?Missing RESTORE_DATABASE or POSTGRES_DB for host restore}"

  PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$RESTORE_ADMIN_DATABASE" \
    -v ON_ERROR_STOP=1 \
    --set target_db="$RESTORE_DATABASE" <<'SQL'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = :'target_db'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS :"target_db";
CREATE DATABASE :"target_db";
SQL
}

run_host_restore() {
  if ! command_exists pg_restore; then
    die "pg_restore is required for RESTORE_MODE=host."
  fi

  if [[ "$RESTORE_RECREATE_DATABASE" == "1" ]]; then
    run_host_recreate_database
  fi

  if [[ -n "${RESTORE_DATABASE:-}" ]]; then
    : "${POSTGRES_USER:?Missing POSTGRES_USER for host restore}"

    PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_restore \
      --host="$POSTGRES_HOST" \
      --port="$POSTGRES_PORT" \
      --username="$POSTGRES_USER" \
      --clean \
      --if-exists \
      --no-owner \
      --no-privileges \
      --dbname="$RESTORE_DATABASE" \
      "$BACKUP_FILE"
    return
  fi

  if [[ -n "${RESTORE_DATABASE_URL:-}" ]]; then
    pg_restore \
      --clean \
      --if-exists \
      --no-owner \
      --no-privileges \
      --dbname="$RESTORE_DATABASE_URL" \
      "$BACKUP_FILE"
    return
  fi

  die "Set RESTORE_DATABASE_URL or POSTGRES_* / RESTORE_DATABASE for host restore."
}

run_docker_recreate_database() {
  : "${RESTORE_DATABASE:?Missing RESTORE_DATABASE or POSTGRES_DB for docker restore}"

  docker compose exec -T \
    -e RESTORE_DATABASE="$RESTORE_DATABASE" \
    -e RESTORE_ADMIN_DATABASE="$RESTORE_ADMIN_DATABASE" \
    "$DOCKER_POSTGRES_SERVICE" sh -lc '
      set -e

      PGPASSWORD="${POSTGRES_PASSWORD:-}" psql \
        --host=127.0.0.1 \
        --port=5432 \
        --username="${POSTGRES_USER}" \
        --dbname="${RESTORE_ADMIN_DATABASE}" \
        -v ON_ERROR_STOP=1 \
        --set target_db="${RESTORE_DATABASE}" <<'"'"'SQL'"'"'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = :'target_db'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS :"target_db";
CREATE DATABASE :"target_db";
SQL
    '
}

run_docker_restore() {
  if ! has_docker_compose; then
    die "docker compose is required for RESTORE_MODE=docker."
  fi

  : "${RESTORE_DATABASE:?Missing RESTORE_DATABASE or POSTGRES_DB for docker restore}"

  if [[ "$RESTORE_RECREATE_DATABASE" == "1" ]]; then
    run_docker_recreate_database
  fi

  docker compose exec -T \
    -e RESTORE_DATABASE="$RESTORE_DATABASE" \
    "$DOCKER_POSTGRES_SERVICE" sh -lc '
      set -euo pipefail

      temp_restore_file="/tmp/restore-$$.dump"
      trap '\''rm -f -- "$temp_restore_file"'\'' EXIT

      cat > "$temp_restore_file"

      PGPASSWORD="${POSTGRES_PASSWORD:-}" exec pg_restore \
        --host=127.0.0.1 \
        --port=5432 \
        --username="${POSTGRES_USER}" \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --dbname="${RESTORE_DATABASE}" \
        "$temp_restore_file"
    ' < "$BACKUP_FILE"
}

if [[ -z "$BACKUP_FILE" ]]; then
  usage
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  die "Backup file not found: $BACKUP_FILE"
fi

if [[ "$RESTORE_RECREATE_DATABASE" != "0" && "$RESTORE_RECREATE_DATABASE" != "1" ]]; then
  die "RESTORE_RECREATE_DATABASE must be 0 or 1."
fi

EXECUTION_BACKEND="$(resolve_mode)"

case "$EXECUTION_BACKEND" in
  host)
    run_host_restore
    ;;
  docker)
    run_docker_restore
    ;;
esac

printf 'Restore completed from: %s\n' "$BACKUP_FILE"
printf 'Execution mode: %s\n' "$EXECUTION_BACKEND"
if [[ -n "${RESTORE_DATABASE:-}" ]]; then
  printf 'Target database: %s\n' "$RESTORE_DATABASE"
fi
