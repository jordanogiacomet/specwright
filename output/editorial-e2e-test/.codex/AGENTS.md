# AGENTS.md

## Project: Editorial E2E Test

Editorial validation run

## Context

- App shape: unknown
- Audience: unknown
- Surface: admin_plus_public_site
- Stack: nextjs + payload + postgres
- Capabilities: cms, public-site
- Features: authentication, roles, media-library, draft-publish, preview, scheduled-publishing
- Core work features: none specified

## How to work

You are implementing this project story-by-story.
The ralph.sh script will tell you which story to implement.

1. Read the story file passed to you
2. Read `spec.json` for full context when needed
3. Read `architecture.md` for component structure
4. Implement the story with minimal, targeted changes
5. Run validation if commands are available
6. Do NOT change architecture or scope beyond what the story requires

## Read these files for context

- `spec.json` — full project specification (source of truth)
- `PRD.md` — product requirements
- `architecture.md` — system components and decisions
- `decisions.md` — stable architectural decisions
- `docs/stories/` — all story definitions

## Scope boundaries

- Do NOT add i18n, localization, or multi-language features
- Do NOT add background workers, cron jobs, or scheduled tasks
- Do NOT redesign the architecture
- Do NOT add features not listed in the spec
- Do NOT skip to later stories — implement only what is asked
- Do NOT create files in `src/pages/` — this project uses the App Router (`src/app/`) exclusively
- Use environment variable names exactly as defined in `.env.example` — do NOT rename or invent alternatives (e.g. use `NEXT_PUBLIC_API_URL` not `NEXT_PUBLIC_API_BASE_URL`)

## Project structure

Layout: Next.js + Payload monorepo (single package.json)

### Directories

```
src/app                                   # Next.js app router — route groups and pages
src/app/(app)                             # Admin/authenticated application routes
src/collections                           # Payload CMS collection definitions
src/globals                               # Payload CMS global definitions
src/components                            # Shared React UI components
src/components/ui                         # Base UI primitives (Button, Input, Modal, etc.)
src/lib                                   # Shared utilities, helpers, and business logic
src/hooks                                 # Custom React hooks
src/styles                                # Global styles and Tailwind config
docker                                    # Docker and docker-compose files
src/app/(public)                          # Public-facing routes (marketing, content)
src/app/(auth)                            # Auth routes (login, register, etc.)
src/collections/Media.ts                  # Payload Media collection with upload config
docs/stories                              # Story files for agent execution
```

### Root files

```
package.json                              # Dependencies and npm scripts
tsconfig.json                             # TypeScript configuration
.eslintrc.js                              # ESLint configuration (or eslint.config.js)
.prettierrc                               # Prettier configuration
.env.example                              # Environment variable template
.gitignore                                # Git ignore rules
docker-compose.yml                        # Docker services (database, etc.)
README.md                                 # Project documentation
```

Create files in these locations. Do NOT invent a different directory structure.

## Domain model

### Entities

**User**: System user with authentication credentials and role assignment.
  States: active → disabled

**Article**: Editorial content item managed through a draft-to-publish workflow.
  States: draft → in_review → published → scheduled → archived
  Relationships: belongs_to User (as author), has_many MediaAsset, has_many Category

**Category**: Taxonomy for organizing and filtering content.
  Relationships: has_many Article

**MediaAsset**: Uploaded image, document, or file managed in the media library.
  Relationships: belongs_to User (as uploader)

### Roles

- **admin**: manage_users, manage_config, publish, archive, delete_content, manage_categories, manage_media
- **editor**: create_article, edit_own_article, submit_for_review, upload_media, manage_own_media
- **reviewer**: approve_article, reject_article, edit_any_article, publish, view_all_articles

### Auth: email_password, session: jwt (Payload built-in)

Implement entities, states, and permissions as described above.

## Security requirements

- Use `process.env.PAYLOAD_SECRET` (or `JWT_SECRET`) — NEVER hardcode secrets or use fallback values
- Password fields MUST enforce `minLength: 8` on both client and server
- Auth endpoints (`/api/users/login`, `/api/users/create`, `/api/auth/login`, `/api/auth/register`) MUST have rate limiting (e.g. `express-rate-limit` or Next.js middleware)
- All env vars defined in `.env.example` that are referenced in code MUST be imported and used — do not define unused variables
- NEVER commit `.env.local` or any file containing real secrets

## TypeScript conventions

- Use TypeScript (`.ts`/`.tsx`) exclusively — do NOT create `.js`/`.jsx` files alongside `.ts` files
- If a module exists as `.ts`, NEVER create a `.js` re-export or duplicate
- Import Payload collections using `.ts` extension when `allowImportingTsExtensions` is enabled

## Database migrations — CRITICAL

**Every time you modify a collection, model, or database schema, you MUST generate and run a migration.**

This includes:
- Adding or removing fields on a collection
- Creating a new collection
- Adding localization to fields
- Changing field types or validation rules
- Adding relationships between collections

**Migration directory: `src/lib/migrations/`** — ALL migration files MUST go here. Do NOT create migrations in any other directory (e.g. `src/models/migrations/`).

Migration workflow:
1. Make the schema change (edit collection file)
2. Generate a migration: `npm run db:migrate:create`
3. Implement the migration (use `_pgm` as the parameter name to avoid lint warnings, e.g. `exports.up = (_pgm) => { ... }`)
4. Run the migration: `npm run db:migrate`
5. Verify the migration ran: `npm run db:migrate:status`

**If you skip this step, the application will crash at runtime with "relation does not exist" errors.**

The ralph.sh script will also run `npm run db:migrate` after your story completes as a safety net, but you should generate the migration yourself as part of the story implementation.

## Validation

After implementing a story, run in this order (if available):

1. Generate and run migrations if schema changed: `npm run db:migrate`
2. `npm test` or equivalent test command
3. `npm run lint` or equivalent lint command
4. `npm run build` or equivalent build command

Record results. If a command doesn't exist yet, note that.

## Stack details

- Frontend: nextjs
- Backend: payload
- Database: postgres
- Deploy target: docker
- Migration command: `npm run db:migrate`
