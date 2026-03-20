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

usage() {
  echo "Usage: bash scripts/restore.sh <backup-file> [target-database-uri]" >&2
}

load_env_file "$PROJECT_ROOT/.env"
load_env_file "$PROJECT_ROOT/.env.local"

if (( $# < 1 || $# > 2 )); then
  usage
  exit 1
fi

BACKUP_FILE="$1"
TARGET_DATABASE_URI="${2:-${RESTORE_DATABASE_URI:-${DATABASE_URI:-}}}"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

if [[ -z "$TARGET_DATABASE_URI" ]]; then
  echo "A target database URI is required via the second argument, RESTORE_DATABASE_URI, or DATABASE_URI." >&2
  exit 1
fi

require_command node
require_command psql
require_command pg_restore

uri_info="$(
  TARGET_DATABASE_URI="$TARGET_DATABASE_URI" node <<'NODE'
const uri = process.env.TARGET_DATABASE_URI;

try {
  const targetUrl = new URL(uri);
  const databaseName = decodeURIComponent(targetUrl.pathname.replace(/^\/+/, ""));

  if (!databaseName) {
    throw new Error("TARGET_DATABASE_URI must include a database name.");
  }

  const adminUrl = new URL(uri);
  adminUrl.pathname = "/postgres";

  console.log(databaseName);
  console.log(adminUrl.toString());
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
NODE
)"

readarray -t uri_parts <<<"$uri_info"
TARGET_DATABASE_NAME="${uri_parts[0]:-}"
ADMIN_DATABASE_URI="${uri_parts[1]:-}"

if [[ -z "$TARGET_DATABASE_NAME" || -z "$ADMIN_DATABASE_URI" ]]; then
  echo "Could not parse TARGET_DATABASE_URI." >&2
  exit 1
fi

target_database_literal="${TARGET_DATABASE_NAME//\'/\'\'}"
target_database_identifier="${TARGET_DATABASE_NAME//\"/\"\"}"

database_exists="$(
  psql "$ADMIN_DATABASE_URI" -v ON_ERROR_STOP=1 -Atc \
    "SELECT 1 FROM pg_database WHERE datname = '${target_database_literal}'"
)"

if [[ "$database_exists" != "1" ]]; then
  psql "$ADMIN_DATABASE_URI" -v ON_ERROR_STOP=1 -c \
    "CREATE DATABASE \"${target_database_identifier}\""
fi

pg_restore \
  --clean \
  --if-exists \
  --exit-on-error \
  --no-owner \
  --no-privileges \
  --dbname "$TARGET_DATABASE_URI" \
  "$BACKUP_FILE"

echo "Restore completed into database: $TARGET_DATABASE_NAME"
