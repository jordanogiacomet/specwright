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
2. Generate a migration: `npx payload migrate:create`
3. Run the migration: `npx payload migrate`
4. Verify the migration ran: `npx payload migrate:status`

**If you skip this step, the application will crash at runtime with "relation does not exist" errors.**

The ralph.sh script will also run `npx payload migrate` after your story completes as a safety net, but you should generate the migration yourself as part of the story implementation.

## Validation

After implementing a story, run in this order (if available):

1. Generate and run migrations if schema changed: `npx payload migrate`
2. `npm test` or equivalent test command
3. `npm run lint` or equivalent lint command
4. `npm run build` or equivalent build command

Record results. If a command doesn't exist yet, note that.

## Stack details

- Frontend: nextjs
- Backend: payload
- Database: postgres
- Deploy target: docker
- Migration command: `npx payload migrate`
