#!/usr/bin/env bash
set -euo pipefail

umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.local}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/storage/backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-todo-app-postgres}"
BACKUP_RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-7}"
EXECUTION_MODE="${BACKUP_MODE:-${POSTGRES_EXECUTION_MODE:-auto}}"
DOCKER_POSTGRES_SERVICE="${DOCKER_POSTGRES_SERVICE:-postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

die() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

has_docker_compose() {
  command_exists docker && docker compose version >/dev/null 2>&1
}

is_positive_integer() {
  [[ "$1" =~ ^[1-9][0-9]*$ ]]
}

resolve_mode() {
  case "$EXECUTION_MODE" in
    auto)
      if command_exists pg_dump; then
        printf 'host\n'
        return
      fi

      if has_docker_compose; then
        printf 'docker\n'
        return
      fi

      die "pg_dump is not installed and docker compose is unavailable. Install PostgreSQL client tools or run through Docker Compose."
      ;;
    host | docker)
      printf '%s\n' "$EXECUTION_MODE"
      ;;
    *)
      die "BACKUP_MODE must be one of: auto, host, docker."
      ;;
  esac
}

run_host_backup() {
  if ! command_exists pg_dump; then
    die "pg_dump is required for BACKUP_MODE=host."
  fi

  if [[ -n "${DATABASE_URL:-}" ]]; then
    pg_dump \
      --format=custom \
      --file="$TEMP_FILE" \
      --dbname="$DATABASE_URL"
    return
  fi

  : "${POSTGRES_USER:?Missing POSTGRES_USER or DATABASE_URL}"
  : "${POSTGRES_DB:?Missing POSTGRES_DB or DATABASE_URL}"

  PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump \
    --format=custom \
    --file="$TEMP_FILE" \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB"
}

run_docker_backup() {
  if ! has_docker_compose; then
    die "docker compose is required for BACKUP_MODE=docker."
  fi

  docker compose exec -T "$DOCKER_POSTGRES_SERVICE" sh -lc '
    set -e

    PGPASSWORD="${POSTGRES_PASSWORD:-}" exec pg_dump \
      --format=custom \
      --host=127.0.0.1 \
      --port=5432 \
      --username="${POSTGRES_USER}" \
      --dbname="${POSTGRES_DB}"
  ' > "$TEMP_FILE"
}

prune_old_backups() {
  local -a backup_files=()
  local old_file
  local removed_count=0

  while IFS= read -r -d '' backup_file; do
    backup_files+=("$backup_file")
  done < <(
    find "$BACKUP_DIR" -maxdepth 1 -type f -name "${BACKUP_PREFIX}-*.dump" -print0 |
      sort -z -r
  )

  if ((${#backup_files[@]} <= BACKUP_RETENTION_COUNT)); then
    return
  fi

  for old_file in "${backup_files[@]:BACKUP_RETENTION_COUNT}"; do
    rm -f -- "$old_file"
    removed_count=$((removed_count + 1))
  done

  printf 'Pruned %s old backup(s).\n' "$removed_count"
}

if ! is_positive_integer "$BACKUP_RETENTION_COUNT"; then
  die "BACKUP_RETENTION_COUNT must be a positive integer."
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="$BACKUP_DIR/${BACKUP_PREFIX}-${TIMESTAMP}.dump"
TEMP_FILE="${BACKUP_FILE}.partial"
EXECUTION_BACKEND="$(resolve_mode)"

cleanup() {
  rm -f -- "$TEMP_FILE"
}

trap cleanup EXIT

case "$EXECUTION_BACKEND" in
  host)
    run_host_backup
    ;;
  docker)
    run_docker_backup
    ;;
esac

mv -- "$TEMP_FILE" "$BACKUP_FILE"
trap - EXIT

prune_old_backups

printf 'Backup created: %s\n' "$BACKUP_FILE"
printf 'Execution mode: %s\n' "$EXECUTION_BACKEND"
printf 'Retention count: %s\n' "$BACKUP_RETENTION_COUNT"
