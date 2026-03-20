# Specwright

**PRD-driven project initializer that turns a prompt or structured spec into an executable repo for AI coding agents.**

Specwright takes a product idea, detects the project archetype, derives architecture and stories, scaffolds a runnable application, and prepares execution bundles for Codex/OpenClaw-style story-by-story loops.

```text
"editorial CMS with public site and preview"
    -> archetype detection + optional AI discovery
    -> canonical spec + architecture + domain model + enriched stories
    -> runnable scaffold (Next.js + Payload or Next.js + node-api)
    -> .codex/ + .openclaw/ execution bundle
    -> ./ralph.sh drives Codex story-by-story
```

## What Specwright Generates

- A canonical `spec.json` source of truth
- `PRD.md`, `architecture.md`, `decisions.md`, `constraints.md`, `risks.md`, and a Mermaid architecture diagram
- Enriched stories with acceptance criteria, scope boundaries, dependencies, expected files, and validation hints
- A runnable scaffold with `package.json`, `docker-compose.yml`, `Dockerfile`, `.env.example`, and `.env.local`
- A Codex bundle: `.codex/AGENTS.md` plus `ralph.sh`
- An OpenClaw-style bundle: `.openclaw/execution-plan.json`, `api-contract.json`, track plans, `commands.json`, `manifest.json`, and `repo-contract.json`

## Why

AI coding agents are good at writing code, but weak at deciding what the repo should contain, what is in scope, and how work should be sequenced. Specwright gives the agent a concrete execution contract:

- Deterministic archetype detection and default stack selection
- Optional AI-assisted discovery, challenge resolution, and design-reference analysis
- Derived domain model, architecture contracts, and project structure
- Story-by-story execution metadata, including dependencies and owned files
- Validation commands detected from the generated repo and written to `.openclaw/commands.json`

## Pipeline

```text
project idea / spec file
    -> detect archetype
    -> collect CLI answers
    -> optional --assist discovery + challenge decisions
    -> optional --reference image analysis
    -> derive capabilities, architecture, stories, domain model, risks, design system
    -> write scaffold + docs + execution bundles
    -> optional enrich / prepare
    -> ./ralph.sh executes stories with Codex CLI
```

## Quick Start

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Generate interactively

```bash
initializer new
```

### Generate with AI discovery

```bash
OPENAI_API_KEY=sk-... initializer new --assist
OPENAI_API_KEY=sk-... initializer new --assist --reference ./designs
```

### Generate from a structured file

```bash
# JSON spec
initializer new --spec examples/simple-task-manager.spec.json

# YAML/playbook-style input
initializer new --spec examples/next-payload-postgres.input.yaml
```

### Run the full pipeline

```bash
OPENAI_API_KEY=sk-... initializer run --assist --reference ./designs
```

`initializer run` orchestrates:

```text
new -> enrich -> prepare -> ralph
```

Use `--dry-run` to stop before Codex execution, or `--no-execute` to prepare the project and exit.

### Start the generated project

```bash
cd output/my-project
npm install
docker compose up -d
npm run dev
```

`.env.local` is generated automatically, so there is no copy step before local boot.

### Execute with Codex

```bash
cd output/my-project
./ralph.sh --dry-run
./ralph.sh

# Optional overrides
CODEX_MODEL=gpt-5.4 CODEX_EFFORT=medium ./ralph.sh
```

## Input Formats

Specwright currently accepts three practical input styles:

1. Interactive prompt flow via `initializer new`
2. JSON spec files, such as [`examples/simple-task-manager.spec.json`](examples/simple-task-manager.spec.json)
3. YAML playbook-style inputs with `guided_answers` / `critical_confirmations`, such as [`examples/next-payload-postgres.input.yaml`](examples/next-payload-postgres.input.yaml)

When `--spec` points to a directory, Specwright will resolve `spec.json`, `spec.yaml`, or `spec.yml` automatically.

## CLI Reference

| Command | Purpose |
| --- | --- |
| `initializer new [--assist] [--spec path] [--reference dir]` | Generate a project from an interactive prompt or structured input |
| `initializer run [--assist] [--reference dir] [--dry-run] [--no-execute]` | Full pipeline: generate, enrich, prepare, execute |
| `initializer plan [--spec path]` | Write a lightweight planning package to `plans/<slug>/` |
| `initializer enrich <path> [--review]` | Derive PRD intelligence and optionally AI architecture review |
| `initializer prepare <path>` | Regenerate execution bundles, detect commands, and print execution preview |
| `initializer refine <path>` | Archive the current PRD to `docs/history/` and apply the current refinement pass |
| `initializer doctor [path]` | Check the generated project package for core docs and bundle artifacts |
| `initializer validate [path]` | Validate `spec.json`, semantic spec variants, and `prd.json` when present |
| `initializer benchmark <path> [--candidate path] [--output file] [--json file] [--snapshot-dir dir]` | Compare serial vs parallel execution results from `progress.txt` and git state |
| `initializer architect <path>` | Interactively edit architecture components, communication, boundaries, and decisions |
| `initializer design <path> [--reference dir]` | Interactively edit the design system and optionally analyze references |

## Supported Archetypes

| Archetype | Default stack | Typical features |
| --- | --- | --- |
| `editorial-cms` | `nextjs + payload + postgres` | auth, roles, media-library, draft-publish, preview, scheduled-publishing |
| `marketplace` | `nextjs + node-api + postgres` | auth, payments, search, reviews, notifications |
| `saas-app` | `nextjs + node-api + postgres` | auth, roles, billing, analytics, notifications |
| `backoffice` | `nextjs + node-api + postgres` | auth, roles, api |
| `client-portal` | `nextjs + node-api + postgres` | auth, roles, notifications, api |
| `work-organizer` | `nextjs + node-api + postgres` | auth, roles, api |
| `knowledge-base` | `nextjs + node-api + postgres` | auth, search, api |
| `todo-app` | `nextjs + node-api + postgres` | auth, api |
| `generic-web-app` | `nextjs + node-api + postgres` | auth, api |

## Generated Project Layout

```text
output/my-project/
├── spec.json
├── PRD.md
├── architecture.md
├── decisions.md
├── progress.txt
├── README.md
├── package.json
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .env.local
├── .codex/
│   └── AGENTS.md
├── .openclaw/
│   ├── AGENTS.md
│   ├── OPENCLAW.md
│   ├── api-contract.json
│   ├── commands.json
│   ├── execution-plan.json
│   ├── shared-plan.json
│   ├── frontend-plan.json
│   ├── backend-plan.json
│   ├── integration-plan.json
│   ├── manifest.json
│   └── repo-contract.json
├── docs/
│   ├── stories/
│   ├── constraints.md
│   ├── design-system.md
│   ├── risks.md
│   ├── architecture/
│   │   └── diagram.mmd
│   ├── prd-intelligence.json          # after `initializer enrich`
│   └── architecture-review.json       # after `initializer enrich --review`
├── ralph.sh
└── src/
    ├── app/
    ├── components/
    ├── lib/
    └── __tests__/
```

Payload projects also include `src/payload.config.ts`, `src/collections/Users.ts`, admin route files under `src/app/(payload)/`, and `scripts/payload-migrations.mjs`.

## Parallel Execution Bundle

Specwright does more than emit a flat story list. The generated `.openclaw/` bundle includes:

- `execution-plan.json`: full ordered plan with dependencies and phase metadata
- `api-contract.json`: shared contract between frontend and backend slices
- `shared-plan.json`, `frontend-plan.json`, `backend-plan.json`, `integration-plan.json`: loop-specific track plans
- `commands.json`: detected `test`, `lint`, `build`, `typecheck`, `dev`, and migration commands

`ralph.sh` consumes those files directly and runs Codex with owned-file guidance, retries, validation, migration hooks, and per-track execution metadata.

## Examples

The repository ships with examples you can run directly:

```bash
initializer new --spec examples/simple-task-manager.spec.json
initializer new --spec examples/next-payload-postgres.input.yaml
```

There are also archetype playbooks under [`playbooks/`](playbooks) for built-in defaults such as [`playbooks/editorial-cms.yaml`](playbooks/editorial-cms.yaml).

## Development

```bash
make install
make dev
make test
make test-verbose
make clean
```

## Testing

```bash
.venv/bin/pytest tests -q
```

Current suite size: **451 tests collected** across unit, integration, regression, and e2e coverage.

Covered areas include:

- archetype detection and capability derivation
- assisted discovery merge and signal governance
- story generation and execution metadata
- architecture, domain model, risks, and project structure engines
- bundle generation for Codex/OpenClaw
- scaffold generation for Payload and node-api stacks
- CLI flows such as `new`, `prepare`, `validate`, and benchmark analysis

## Requirements

- Python 3.11+
- `OPENAI_API_KEY` for `--assist`, `--reference`, and `enrich --review`
- Node.js 22+ for generated projects
- Docker for local database services
- `jq`, `npx`, and the Codex CLI for `ralph.sh`
- `flock` for the generated build script on Linux environments (`util-linux` package on most distros)

---

## PT-BR

### O que o projeto faz

O Specwright gera um repositório executável a partir de uma ideia de produto ou de um arquivo estruturado. Ele detecta o archetype, deriva arquitetura e stories, monta o scaffold, gera os bundles de execução em `.codex/` e `.openclaw/`, e deixa o projeto pronto para o `./ralph.sh` tocar story por story com o Codex CLI.

### Fluxo rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

OPENAI_API_KEY=sk-... initializer run --assist --reference ./designs
```

Ou, se quiser partir de arquivos de exemplo:

```bash
initializer new --spec examples/simple-task-manager.spec.json
initializer new --spec examples/next-payload-postgres.input.yaml
```

### Comandos mais úteis

- `initializer new`: gera um projeto novo
- `initializer run`: roda o pipeline completo (`new -> enrich -> prepare -> ralph`)
- `initializer prepare <path>`: reescreve os bundles e detecta comandos reais do repositório
- `initializer doctor <path>`: verifica os artefatos principais do pacote gerado
- `initializer benchmark <path> --candidate <path>`: compara uma execução serial com uma paralela

### Requisitos

- Python 3.11+
- `OPENAI_API_KEY` para fluxos assistidos por IA
- Node.js 22+, Docker, `jq`, `npx`, Codex CLI e `flock` para os projetos gerados

## License

MIT
