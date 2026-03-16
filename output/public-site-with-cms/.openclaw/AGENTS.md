# AGENTS.md

You are an execution agent working on **Public site with cms**.

## What this project is

Public-facing content platform with integrated CMS for external clients, supporting i18n, scheduled jobs, and report generation.

- **App shape**: content-platform
- **Primary audience**: external_clients
- **Surface**: admin_plus_public_site
- **Stack**: nextjs + payload + postgres
- **Capabilities**: cms, public-site, i18n, scheduled-jobs
- **Features**: authentication, roles, media-library, draft-publish, preview, scheduled-publishing
- **Core work features**: report-generation, cms

## Read order

Before changing code, read these files in this order:

1. `spec.json` — structured source of truth
2. `PRD.md` — enriched product requirements
3. `decisions.md` — stable architectural decisions
4. `progress.txt` — append-only execution log
5. `.openclaw/execution-plan.json` — ordered story list with phases
6. `docs/stories/` — individual story files
7. project source files

## Execution rules

- Work **one story at a time**, following the order in `execution-plan.json`
- Start with the **bootstrap phase** — these set up the project structure
- Do not skip ahead to domain stories before features are in place
- Do not silently change architecture or product scope
- Prefer minimal, targeted patches over large rewrites
- Validate after each story when possible
- Append progress to `progress.txt` after meaningful work

## What NOT to do

- Do not add a public-facing site unless `public-site` is in capabilities
- Do not add CMS features unless `cms` is in capabilities
- Do not add i18n unless `i18n` is in capabilities
- Do not redesign the architecture — it was derived from the spec
- Do not merge stories or skip validation steps

## Contract

- `spec.json` is the structured source of truth
- `decisions.md` contains stable decisions unless explicitly superseded
- `progress.txt` is append-only
- Stories under `docs/stories/` define execution slices
- Implementation must follow the generated architecture

## Validation

When relevant, validate in this order:

1. Targeted test for the current story
2. Full test suite
3. Lint
4. Build

If a command is unavailable, record that in `progress.txt`.

## Completion standard

A story is complete when:

- Code is changed and working
- Validation was attempted
- Results were recorded in `progress.txt`
- The story requirements are satisfied
