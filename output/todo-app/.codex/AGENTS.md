# AGENTS.md

## Project: todo-app

Simple todo app with authentication and API support featuring deadlines, task assignment, progress tracking, reminders, and report generation. Includes CMS, internationalization, and scheduled jobs support.

## Context

- App shape: generic-web-app
- Audience: mixed
- Surface: admin_plus_public_site
- Stack: nextjs + node-api + postgres
- Capabilities: public-site, cms, scheduled-jobs, i18n
- Features: authentication, api, notifications
- Core work features: deadlines, task-assignment, progress-tracking, reminders, report-generation

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

- No specific restrictions
- Do NOT redesign the architecture
- Do NOT add features not listed in the spec
- Do NOT skip to later stories — implement only what is asked

## Project structure

Layout: Next.js + node-api monorepo (single package.json)

### Directories

```
src/app                                   # Next.js app router — route groups and pages
src/app/(app)                             # Admin/authenticated application routes
src/app/api                               # Next.js API routes or standalone API server
src/components                            # Shared React UI components
src/components/ui                         # Base UI primitives (Button, Input, Modal, etc.)
src/lib                                   # Shared utilities, helpers, and business logic
src/hooks                                 # Custom React hooks
src/models                                # Database models and schema definitions
src/middleware                            # Express/Fastify middleware (auth, logging, etc.)
src/styles                                # Global styles and Tailwind config
docker                                    # Docker and docker-compose files
src/app/(public)                          # Public-facing routes
src/app/(auth)                            # Auth routes (login, register, etc.)
src/jobs                                  # Background job definitions and scheduler
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

**Todo**: A task or action item owned by a user
  States: pending → completed
  Relationships: belongs_to User

**User**: An application user who owns todos
  Relationships: has_many Todo

### Roles

- **user**: create_todo, read_own_todos, update_own_todo, delete_own_todo, toggle_todo_complete

### Auth: email_password, session: jwt

Implement entities, states, and permissions as described above.

## Database migrations — CRITICAL

**Every time you modify a collection, model, or database schema, you MUST generate and run a migration.**

This includes:
- Adding or removing fields on a collection
- Creating a new collection
- Adding localization to fields
- Changing field types or validation rules
- Adding relationships between collections

Migration workflow:
1. Make the schema change (edit collection file)
2. Generate a migration: `npm run db:migrate:create`
3. Run the migration: `npm run db:migrate`
4. Verify the migration ran: `npm run db:migrate:status`

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
- Backend: node-api
- Database: postgres
- Deploy target: docker
- Migration command: `npm run db:migrate`
