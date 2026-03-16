# AGENTS.md

## Project: public site with cms design

A public-facing content platform with an integrated CMS supporting content creation, editing, versioning, user management, publishing workflows, multi-language support, and scheduled/background jobs.

## Context

- App shape: content-platform
- Audience: mixed
- Surface: admin_plus_public_site
- Stack: nextjs + payload + postgres
- Capabilities: cms, public-site, i18n, scheduled-jobs
- Features: authentication, roles, media-library, draft-publish, preview, scheduled-publishing
- Core work features: content-creation, editing, versioning, user-management

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

## Validation

After implementing a story, run in this order (if available):

1. `npm test` or equivalent test command
2. `npm run lint` or equivalent lint command
3. `npm run build` or equivalent build command

Record results. If a command doesn't exist yet, note that.

## Stack details

- Frontend: nextjs
- Backend: payload
- Database: postgres
- Deploy target: docker
