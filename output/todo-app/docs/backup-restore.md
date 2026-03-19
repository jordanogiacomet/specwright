# Database Backup and Restore

## Purpose

This project uses portable PostgreSQL dump files created with `pg_dump` custom format (`-Fc`). The custom format keeps backups compact and compatible with `pg_restore` for selective restores.

## Defaults

- Backup script: `bash scripts/backup.sh`
- Restore script: `bash scripts/restore.sh <backup-file>`
- Default env file: `.env.local`
- Default backup directory: `storage/backups`
- Default retention policy: keep the newest `7` backup files
- Default Docker service name: `postgres`

The scripts load `.env.local` automatically and can also be pointed at another env file with `ENV_FILE=/path/to/file`.

## Configuration

The scripts support these environment overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENV_FILE` | `.env.local` | Env file to source before running backup or restore |
| `BACKUP_DIR` | `storage/backups` | Directory where backup files are written |
| `BACKUP_PREFIX` | `todo-app-postgres` | File prefix for generated dumps |
| `BACKUP_RETENTION_COUNT` | `7` | Number of newest dump files to keep |
| `BACKUP_MODE` | `auto` | Backup execution mode: `auto`, `host`, or `docker` |
| `RESTORE_MODE` | `auto` | Restore execution mode: `auto`, `host`, or `docker` |
| `POSTGRES_EXECUTION_MODE` | unset | Shared default for both scripts if you want one mode for both |
| `DOCKER_POSTGRES_SERVICE` | `postgres` | Docker Compose service name that runs PostgreSQL |
| `POSTGRES_HOST` | `localhost` | Host used by host-side `pg_dump` / `pg_restore` when `DATABASE_URL` is not used |
| `POSTGRES_PORT` | `5432` | Port used by host-side `pg_dump` / `pg_restore` when `DATABASE_URL` is not used |
| `RESTORE_DATABASE` | `POSTGRES_DB` | Target database name for restore |
| `RESTORE_DATABASE_URL` | `DATABASE_URL` | Target connection string for host-mode restore |
| `RESTORE_RECREATE_DATABASE` | `0` | Recreate the target database before restore when set to `1` |
| `RESTORE_ADMIN_DATABASE` | `postgres` | Admin database used for `DROP DATABASE` / `CREATE DATABASE` |

## Backup Modes

### Host mode

If `pg_dump` is available on the machine running the script, `bash scripts/backup.sh` will use it directly.

When `DATABASE_URL` is set, the script uses that connection string. Otherwise it falls back to `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.

### Docker mode

If host PostgreSQL client tools are not installed but `docker compose` is available, the scripts can run against the `postgres` container instead:

```bash
BACKUP_MODE=docker bash scripts/backup.sh
RESTORE_MODE=docker bash scripts/restore.sh storage/backups/<backup-file>.dump
```

The Docker path runs `pg_dump`, `psql`, and `pg_restore` inside the Compose PostgreSQL service, so it works even on hosts without PostgreSQL client packages.

## Retention Policy

The backup script keeps the newest `7` dump files by default and deletes older files with the same prefix in the same backup directory.

If you schedule one backup per day, this policy keeps the last 7 daily restore points.

Change the retention count if needed:

```bash
BACKUP_RETENTION_COUNT=14 bash scripts/backup.sh
```

## Creating a Backup

Run the backup script from the repository root:

```bash
bash scripts/backup.sh
```

Example output:

```text
Backup created: storage/backups/todo-app-postgres-20260318T120000Z.dump
Execution mode: host
Retention count: 7
```

## Restore Procedure

Restoring into a scratch database is the safest manual validation path because it avoids overwriting the main development database.

### 1. Create a backup

```bash
bash scripts/backup.sh
```

### 2. Restore into a test database

Host mode example:

```bash
RESTORE_DATABASE=todo_app_restore_test \
RESTORE_RECREATE_DATABASE=1 \
bash scripts/restore.sh storage/backups/todo-app-postgres-<timestamp>.dump
```

Docker mode example:

```bash
RESTORE_MODE=docker \
RESTORE_DATABASE=todo_app_restore_test \
RESTORE_RECREATE_DATABASE=1 \
bash scripts/restore.sh storage/backups/todo-app-postgres-<timestamp>.dump
```

### 3. Verify the restored database manually

Examples:

```bash
psql postgresql://postgres:postgres@localhost:5433/todo_app_restore_test -c '\dt'
psql postgresql://postgres:postgres@localhost:5433/todo_app_restore_test -c 'select count(*) from todos;'
```

If you restored through Docker and do not have `psql` locally, run the same checks inside the container:

```bash
docker compose exec -T postgres psql -U postgres -d todo_app_restore_test -c '\dt'
```

### 4. Optional cleanup

```bash
psql postgresql://postgres:postgres@localhost:5433/postgres -c 'drop database if exists todo_app_restore_test;'
```

## Suggested Scheduling

Example daily cron entry:

```bash
0 2 * * * cd /path/to/todo-app && bash scripts/backup.sh >> /var/log/todo-app-backup.log 2>&1
```

This story intentionally stops at portable periodic backups. Monitoring, alerting, cloud snapshots, and replication are out of scope.
