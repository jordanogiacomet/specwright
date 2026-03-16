# public site with cms design

Repository bootstrap for a Next.js application with Payload CMS and Postgres.

This story sets up the project foundation only. There are no collections, authentication rules, or business features yet.

## Prerequisites

- Node.js 24+
- npm 10+
- Docker (for the local Postgres container)

## Quick Start

```bash
cp .env.example .env.local
npm install
docker compose up -d
npm run dev
```

The placeholder app runs at `http://localhost:3000`.

## Scripts

- `npm run dev` starts the Next.js development server
- `npm run build` creates a production build
- `npm run lint` runs ESLint
- `npm run typecheck` runs the TypeScript compiler in no-emit mode
- `npm test` runs the current placeholder test command

## Project Files

- `src/app` contains the Next.js App Router entrypoint
- `payload.config.ts` contains the minimal Payload configuration
- `.env.example` documents the required local environment variables
- `docker-compose.yml` starts the local Postgres dependency

## Reference

- `spec.json` is the project specification
- `architecture.md` describes the target component structure
