# Specwright

**PRD-driven project initializer for AI coding agents.**

Specwright turns a project idea into a complete execution package that Codex, Claude Code, or any AI coding agent can implement story-by-story — with zero ambiguity about what to build.

```
"internal backoffice for operations team to manage orders and generate reports"
    ↓
spec.json + PRD.md + architecture.md + 16 stories + ralph.sh
    ↓
./ralph.sh → Codex implements story-by-story → working project
```

## Why

AI coding agents are powerful but directionless. They can write code, but they don't know *what* to build. Today's workflow is: paste a vague prompt, get something half-right, spend hours correcting drift.

Specwright fixes this by creating a **structured execution contract** between you and the agent:

- **Deterministic planning** — archetype detection, capability derivation, architecture decisions, all rule-based
- **AI-assisted discovery** — asks smart follow-up questions, refines the spec based on your answers
- **Signal governance** — separates what the AI inferred from what you confirmed; your answers always win
- **Scope boundaries** — the agent knows exactly what NOT to do (no CMS if you said no CMS)
- **Story-by-story execution** — the ralph loop feeds one story at a time to Codex, validates, records progress

## The Pipeline

```
You describe a project
    → Specwright detects the archetype (backoffice, client-portal, editorial-cms, etc.)
    → Asks CLI questions (surface, deploy target)
    → Runs AI-assisted discovery (follow-up questions)
    → Generates a canonical spec with confirmed signals
    → Derives architecture, stories, constraints, risks, design system
    → Writes the execution package

Optional: enrich with PRD intelligence (personas, success metrics, scope)
Optional: OpenClaw reads .openclaw/ and standardizes for the executor

Then: ./ralph.sh iterates stories through Codex CLI
```

## Quick Start

### Install

```bash
pip install -e .
```

### Generate a project

```bash
# Interactive mode with AI discovery
OPENAI_API_KEY=sk-... initializer new --assist

# Without AI (deterministic only)
initializer new
```

### Enrich (optional)

```bash
initializer enrich output/my-project
```

### Execute with Codex

```bash
cd output/my-project
./ralph.sh --dry-run    # preview the execution plan
./ralph.sh              # run for real
./ralph.sh --from ST-005  # resume from a specific story
```

## What Gets Generated

```
output/my-project/
├── spec.json                    # structured source of truth
├── PRD.md                       # product requirements
├── architecture.md              # components and tech choices
├── decisions.md                 # architectural decisions
├── progress.txt                 # append-only execution log
├── ralph.sh                     # story-by-story Codex runner
├── .codex/
│   └── AGENTS.md                # instructions for Codex CLI
├── .openclaw/
│   ├── AGENTS.md                # instructions for OpenClaw
│   ├── OPENCLAW.md              # handoff document
│   ├── execution-plan.json      # ordered stories with phases
│   ├── manifest.json            # project metadata
│   ├── repo-contract.json       # contract rules
│   └── commands.json            # validation commands
└── docs/
    ├── stories/
    │   ├── ST-001.md ... ST-016.md
    ├── constraints.md
    ├── design-system.md
    ├── risks.md
    └── architecture/
        └── diagram.mmd
```

## Supported Archetypes

| Archetype | Detected from | Default features |
|-----------|--------------|------------------|
| `editorial-cms` | "cms", "editorial", "blog", "publishing" | auth, roles, media-library, draft-publish, preview, scheduled-publishing |
| `marketplace` | "marketplace", "ecommerce", "store" | auth, payments, search, reviews, notifications |
| `saas-app` | "saas", "subscription", "multi-tenant" | auth, roles, billing, analytics, notifications |
| `backoffice` | "backoffice", "operations team", "manage orders" | auth, roles, api |
| `client-portal` | "client portal", "submit requests", "approvals" | auth, roles, notifications, api |
| `work-organizer` | "work organizer", "task management", "organize work" | auth, roles, api |
| `knowledge-base` | "wiki", "knowledge base", "documentation" | auth, search, api |
| `generic-web-app` | fallback | auth, api |

The AI discovery refines the archetype with `app_shape`, `primary_audience`, `core_work_features`, and boolean signals like `needs_public_site`, `needs_cms`, `needs_i18n`, `needs_scheduled_jobs`.

## Signal Governance

Specwright distinguishes between:

| Signal type | Source | Priority |
|-------------|--------|----------|
| **Inferred** | AI discovery engine | Low |
| **Confirmed** | Your followup answers | High |
| **Effective** | Merged result | Used by all engines |

Your confirmed answers always override AI inference. If you say "no CMS", CMS is removed from capabilities, architecture decisions, design system components, risks — everywhere.

## Commands

```bash
initializer new [--assist] [--spec path]   # generate a project
initializer enrich <path> [--review]       # enrich with intelligence
initializer plan --spec <path>             # generate a plan from existing spec
initializer validate <path>                # validate a generated project
```

## Testing

```bash
pip install pytest
python -m pytest tests -q
```

89 tests covering: archetype detection, capability derivation, signal governance, story generation, bundle generation, enrich flow, public-site leak prevention, and e2e editorial pipeline.

## Architecture

The system is a pipeline of deterministic engines with an optional AI layer on top:

```
prompt → archetype_engine → capability_derivation → capability_engine
    → knowledge_engine → architecture_engine → story_engine
    → refine_engine → constraint_engine → design_system_engine
    → risk_engine → diagram_engine → writers → output
```

AI enters at two points:
1. **Discovery** (`--assist`) — before capability derivation, to refine the spec
2. **Enrich** — after generation, to add PRD intelligence

The AI never replaces the deterministic pipeline. It refines inputs to it.

## Requirements

- Python 3.11+
- `OPENAI_API_KEY` for `--assist` and `enrich --review`
- Node.js + npx for `ralph.sh` (Codex CLI)
- jq for `ralph.sh`

---

## PT-BR

### O que é o Specwright

Specwright é um inicializador de projetos orientado por PRD. Você descreve um projeto em texto livre, ele detecta o tipo, faz perguntas inteligentes, e gera um pacote completo que um agente de IA (Codex, Claude Code) consegue implementar story-by-story.

### Por que isso importa

Agentes de IA são poderosos mas não sabem *o que* construir. O Specwright cria um **contrato de execução estruturado**: spec canônico, architecture decisions, stories ordenadas por fase, scope boundaries claros. O agente recebe uma story de cada vez e sabe exatamente o que fazer e o que não fazer.

### Fluxo

```
Você descreve o projeto
    → Specwright detecta o archetype
    → Faz perguntas no CLI
    → Roda discovery assistida por IA
    → Gera spec refinado com sinais confirmados
    → Deriva architecture, stories, constraints, risks
    → Escreve o pacote de execução

Depois: ./ralph.sh itera stories pelo Codex CLI
```

### Como usar

```bash
pip install -e .

# Gerar projeto com discovery assistida
OPENAI_API_KEY=sk-... initializer new --assist

# Enriquecer com intelligence
initializer enrich output/meu-projeto

# Rodar com Codex
cd output/meu-projeto
./ralph.sh --dry-run
./ralph.sh
```

### Governança de sinais

O Specwright separa sinais inferidos pela IA de sinais confirmados por você. Suas respostas sempre vencem. Se você diz "sem CMS", CMS é removido de capabilities, architecture, design system, risks — em todo lugar.

---

## License

MIT