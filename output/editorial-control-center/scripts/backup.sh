#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

load_env_file() {
  local env_file="$1"

  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$env_file"
    set +a
  fi
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "$command_name is required to run this script." >&2
    exit 1
  fi
}

load_env_file "$PROJECT_ROOT/.env"
load_env_file "$PROJECT_ROOT/.env.local"

if [[ -z "${DATABASE_URI:-}" ]]; then
  echo "DATABASE_URI must be set in the environment, .env, or .env.local." >&2
  exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-7}"
BACKUP_FILENAME_PREFIX="${BACKUP_FILENAME_PREFIX:-editorial-control-center}"
BACKUP_TIMESTAMP="${BACKUP_TIMESTAMP:-$(date -u +"%Y%m%dT%H%M%SZ")}"

if ! [[ "$BACKUP_RETENTION_COUNT" =~ ^[0-9]+$ ]] || (( BACKUP_RETENTION_COUNT < 1 )); then
  echo "BACKUP_RETENTION_COUNT must be a positive integer." >&2
  exit 1
fi

require_command pg_dump

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/${BACKUP_FILENAME_PREFIX}-${BACKUP_TIMESTAMP}.dump"

pg_dump \
  --format=custom \
  --compress=9 \
  --no-owner \
  --no-privileges \
  --file "$BACKUP_FILE" \
  "$DATABASE_URI"

mapfile -t backup_files < <(
  find "$BACKUP_DIR" -maxdepth 1 -type f -name "${BACKUP_FILENAME_PREFIX}-*.dump" | sort -r
)

if (( ${#backup_files[@]} > BACKUP_RETENTION_COUNT )); then
  for stale_backup in "${backup_files[@]:BACKUP_RETENTION_COUNT}"; do
    rm -f "$stale_backup"
  done
fi

echo "Backup created: $BACKUP_FILE"
echo "Retention: kept newest $BACKUP_RETENTION_COUNT backup(s) in $BACKUP_DIR"
