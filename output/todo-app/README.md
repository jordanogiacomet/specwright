# todo-app

Bootstrap repository for a todo application built with Next.js, a standalone Node API, and PostgreSQL.

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Review local environment defaults
cat .env.local

# 3. Start postgres
docker compose up -d

# 4. Start the frontend scaffold
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment

The repository includes:

- `.env.example` as the template for required local variables
- `.env.local` with working local defaults for the frontend, planned API port, and postgres container

## Commands

| Command | Description |
| --- | --- |
| `npm run dev` | Start the Next.js development server |
| `npm run build` | Build the current application scaffold |
| `npm run lint` | Run ESLint across the repository |
| `npm run typecheck` | Run the TypeScript compiler without emitting files |
| `npm test` | Placeholder test command for the bootstrap stage |
| `docker compose up -d` | Start postgres |
| `docker compose down` | Stop postgres |

## Project Structure

- `src/app` contains the Next.js App Router scaffold
- `src/api` is reserved for the standalone Node API stories
- `src/components`, `src/hooks`, `src/lib`, `src/middleware`, `src/models`, `src/jobs`, and `src/styles` provide the shared project layout
- `docker-compose.yml` provisions the local postgres service

See `spec.json`, `architecture.md`, and `docs/stories/` for the full implementation plan.

## Validation

```bash
npm install
npm run lint
npm run build
```
