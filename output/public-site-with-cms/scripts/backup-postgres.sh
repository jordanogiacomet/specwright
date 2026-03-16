#!/bin/sh

set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-public-site-with-cms}"
BACKUP_INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-86400}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
BACKUP_RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-7}"
BACKUP_POSTGRES_HOST="${BACKUP_POSTGRES_HOST:-postgres}"
BACKUP_POSTGRES_PORT="${BACKUP_POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-public_site_with_cms}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

log() {
  printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

is_non_negative_integer() {
  case "$1" in
    ''|*[!0-9]*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

is_positive_integer() {
  if ! is_non_negative_integer "$1"; then
    return 1
  fi

  [ "$1" -gt 0 ]
}

require_setting() {
  value="$1"
  name="$2"

  if [ -z "$value" ]; then
    log "missing required setting: $name"
    exit 1
  fi
}

validate_configuration() {
  require_setting "$BACKUP_DIR" "BACKUP_DIR"
  require_setting "$BACKUP_PREFIX" "BACKUP_PREFIX"
  require_setting "$BACKUP_POSTGRES_HOST" "BACKUP_POSTGRES_HOST"
  require_setting "$BACKUP_POSTGRES_PORT" "BACKUP_POSTGRES_PORT"
  require_setting "$POSTGRES_DB" "POSTGRES_DB"
  require_setting "$POSTGRES_USER" "POSTGRES_USER"

  if ! is_positive_integer "$BACKUP_INTERVAL_SECONDS"; then
    log "BACKUP_INTERVAL_SECONDS must be a positive integer"
    exit 1
  fi

  if ! is_non_negative_integer "$BACKUP_RETENTION_DAYS"; then
    log "BACKUP_RETENTION_DAYS must be a non-negative integer"
    exit 1
  fi

  if ! is_non_negative_integer "$BACKUP_RETENTION_COUNT"; then
    log "BACKUP_RETENTION_COUNT must be a non-negative integer"
    exit 1
  fi
}

wait_for_database() {
  log "waiting for postgres at ${BACKUP_POSTGRES_HOST}:${BACKUP_POSTGRES_PORT}"

  until PGPASSWORD="$POSTGRES_PASSWORD" pg_isready \
    -h "$BACKUP_POSTGRES_HOST" \
    -p "$BACKUP_POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" >/dev/null 2>&1
  do
    sleep 2
  done

  log "postgres is ready"
}

prune_by_age() {
  if [ "$BACKUP_RETENTION_DAYS" -eq 0 ]; then
    return
  fi

  find "$BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name "${BACKUP_PREFIX}-*.dump" \
    -mtime "+${BACKUP_RETENTION_DAYS}" | while IFS= read -r backup_file
  do
    if [ -n "$backup_file" ]; then
      rm -f "$backup_file"
      log "pruned expired backup: $backup_file"
    fi
  done
}

prune_by_count() {
  if [ "$BACKUP_RETENTION_COUNT" -eq 0 ]; then
    return
  fi

  backup_count=$(
    find "$BACKUP_DIR" \
      -maxdepth 1 \
      -type f \
      -name "${BACKUP_PREFIX}-*.dump" | wc -l | tr -d ' '
  )

  if [ "$backup_count" -le "$BACKUP_RETENTION_COUNT" ]; then
    return
  fi

  prune_count=$((backup_count - BACKUP_RETENTION_COUNT))

  find "$BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name "${BACKUP_PREFIX}-*.dump" \
    | sort \
    | head -n "$prune_count" | while IFS= read -r backup_file
  do
    if [ -n "$backup_file" ]; then
      rm -f "$backup_file"
      log "pruned excess backup: $backup_file"
    fi
  done
}

run_backup() {
  timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  output_file="${BACKUP_DIR}/${BACKUP_PREFIX}-${timestamp}.dump"

  mkdir -p "$BACKUP_DIR"

  log "starting backup: $output_file"

  if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$BACKUP_POSTGRES_HOST" \
    -p "$BACKUP_POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --compress=9 \
    --clean \
    --file "$output_file" \
    --format=custom \
    --if-exists \
    --no-owner \
    --no-privileges
  then
    log "backup completed: $output_file"
    prune_by_age
    prune_by_count
  else
    rm -f "$output_file"
    log "backup failed"
    return 1
  fi
}

main() {
  validate_configuration
  wait_for_database

  while true
  do
    if ! run_backup; then
      log "retrying after ${BACKUP_INTERVAL_SECONDS}s"
    fi

    sleep "$BACKUP_INTERVAL_SECONDS"
  done
}

main "$@"
