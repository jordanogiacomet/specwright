# Backup and Restore

`scripts/backup.sh` creates PostgreSQL backups with `pg_dump` in custom format (`-Fc`) so dumps stay compressed and can be restored selectively with `pg_restore`.

## Configuration

The scripts read `.env` and `.env.local` automatically. You can override any value with exported environment variables.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URI` | from `.env.local` | Source database for backups and default target for restores |
| `BACKUP_DIR` | `./backups` | Directory where backup files are written |
| `BACKUP_RETENTION_COUNT` | `7` | Number of most recent dumps to keep |
| `BACKUP_FILENAME_PREFIX` | `editorial-control-center` | Prefix for generated backup files |
| `RESTORE_DATABASE_URI` | unset | Optional default restore target if the second restore argument is omitted |

## Backup Policy

Retention is count-based: the script keeps the newest `7` dump files and deletes older ones from `BACKUP_DIR`. When the script is scheduled once per day, this implements the required "keep the last 7 daily backups" policy.

Example daily cron entry:

```bash
0 2 * * * cd /path/to/editorial-control-center && BACKUP_DIR=/var/backups/editorial-control-center bash scripts/backup.sh
```

## Running Backups

From the host machine:

```bash
bash scripts/backup.sh
```

From a Docker-attached environment, point `DATABASE_URI` at the Postgres service name instead of `localhost`:

```bash
DATABASE_URI=postgresql://postgres:postgres@postgres:5432/editorial_control_center \
  bash scripts/backup.sh
```

## Restore Procedure

1. Choose the backup file to restore.
2. Pick a target database URI. For test restores, use a temporary database name.
3. Run `bash scripts/restore.sh <backup-file> <target-database-uri>`.
4. Verify the restored schema and data with `psql`.

Example test restore:

```bash
BACKUP_FILE=backups/editorial-control-center-20260320T132500Z.dump
TEST_DATABASE_URI=postgresql://postgres:postgres@localhost:5491/editorial_control_center_restore_test

bash scripts/restore.sh "$BACKUP_FILE" "$TEST_DATABASE_URI"
psql "$TEST_DATABASE_URI" -Atc "select count(*) from information_schema.tables where table_schema = 'public';"
```

Notes:

- `scripts/restore.sh` creates the target database automatically if it does not exist.
- Restore into the primary application database only during a maintenance window with the app stopped or disconnected.
- Because the dump format is custom, you can also inspect or restore individual objects with `pg_restore --list` and `pg_restore --table ...`.

## Manual Test Record

Manually tested on March 20, 2026 against the local Docker PostgreSQL instance on port `5491`.

- `bash scripts/backup.sh` created `backups/editorial-control-center-20260320T132241Z.dump`.
- `bash scripts/restore.sh backups/editorial-control-center-20260320T132241Z.dump postgresql://postgres:postgres@localhost:5491/editorial_control_center_restore_test` restored successfully.
- `psql` verification showed `8` tables in the restored database, matching the source database at the time of the test.
- The temporary `editorial_control_center_restore_test` database was dropped after verification.
