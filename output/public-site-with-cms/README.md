# Public site with cms

Bootstrap repository for a public site backed by Next.js, Payload, and Postgres.

This story sets up project scaffolding only. Feature work such as content models, authentication, and business logic belongs to later stories.

## Quick Start

```bash
npm install
cp .env.example .env.local
docker compose up -d
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run lint` | Run ESLint |
| `npm run generate:types` | Generate Payload TypeScript types |
| `npm run typecheck` | Run TypeScript check |
| `npm test` | Run tests |
| `docker compose up -d` | Start postgres |
| `docker compose down` | Stop postgres |

## Backups

`docker compose up -d` now starts a `postgres-backup` sidecar alongside Postgres. It creates compressed Postgres archive backups in the `db_backups` Docker volume on a configurable interval and prunes old backups using both age-based and count-based retention.

Relevant environment variables:

- `BACKUP_DIR` default `/backups`
- `BACKUP_PREFIX` default `public-site-with-cms`
- `BACKUP_INTERVAL_SECONDS` default `86400`
- `BACKUP_RETENTION_DAYS` default `7`
- `BACKUP_RETENTION_COUNT` default `7`

## Validation

```bash
npm run lint
npm run build
npm test
```

## Observability

Backend routes and workers emit structured JSON logs, server-side request failures are tracked through Next's instrumentation hook, and `/api/health` reports the active monitoring configuration.

## Project Structure

See `spec.json` for the full specification, `architecture.md` for the component layout, and `docs/stories/` for the implementation plan.
