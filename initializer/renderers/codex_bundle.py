"""Codex Execution Bundle Generator.

Generates files in the output directory that the Codex CLI
reads directly during the ralph loop:

- .codex/AGENTS.md — instructions the Codex CLI reads automatically
- ralph.sh — shell script that iterates stories via Codex CLI

Key change: ralph.sh now runs database migrations automatically after
each story, and the AGENTS.md and prompt include migration instructions.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any

from initializer.engine.validation_contract import migration_commands


def _get_decision_signals(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _detect_migration_commands(spec: dict[str, Any]) -> dict[str, str]:
    """Detect migration commands based on the backend stack.

    Returns a dict with keys: run, create, status.
    """
    return migration_commands(spec)


def _detect_migration_command(spec: dict[str, Any]) -> str:
    """Backwards-compatible: return the run command."""
    return _detect_migration_commands(spec)["run"]


def _build_agents_md(spec: dict[str, Any]) -> str:
    """Build AGENTS.md for the Codex CLI (.codex/ directory)."""
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    project_name = answers.get("project_name", "Generated Project")
    summary = answers.get("summary", "")
    surface = answers.get("surface", "unknown")
    app_shape = signals.get("app_shape", "unknown")
    primary_audience = signals.get("primary_audience", "unknown")
    core_work_features = signals.get("core_work_features", [])
    if not isinstance(core_work_features, list):
        core_work_features = []

    cap_text = ", ".join(capabilities) if capabilities else "none"
    feat_text = ", ".join(features) if features else "none"
    cwf_text = ", ".join(core_work_features) if core_work_features else "none specified"

    # Build the "do not" rules from capabilities
    do_not_rules = []
    if "public-site" not in capabilities:
        do_not_rules.append("- Do NOT add a public-facing site, CDN, SSR/ISR, or SEO features")
    if "cms" not in capabilities:
        do_not_rules.append("- Do NOT add CMS, content management, or editorial features")
    if "i18n" not in capabilities:
        do_not_rules.append("- Do NOT add i18n, localization, or multi-language features")
    if "scheduled-jobs" not in capabilities:
        do_not_rules.append("- Do NOT add background workers, cron jobs, or scheduled tasks")

    do_not_section = "\n".join(do_not_rules) if do_not_rules else "- No specific restrictions"

    migration_cmds = _detect_migration_commands(spec)
    migration_cmd = migration_cmds["run"]
    migration_create = migration_cmds["create"]
    migration_status = migration_cmds["status"]
    backend = stack.get("backend", "unknown")

    # --- Project structure section ---
    project_structure = spec.get("project_structure", {})
    structure_section = ""
    if project_structure:
        root_type = project_structure.get("root_type", "")
        directories = project_structure.get("directories", [])
        root_files = project_structure.get("root_files", [])

        lines = [f"\n## Project structure\n"]
        if root_type:
            lines.append(f"Layout: {root_type}\n")

        if directories:
            lines.append("### Directories\n")
            lines.append("```")
            for d in directories:
                lines.append(f"{d['path']:40s}  # {d['purpose']}")
            lines.append("```\n")

        if root_files:
            lines.append("### Root files\n")
            lines.append("```")
            for f in root_files:
                lines.append(f"{f['path']:40s}  # {f['purpose']}")
            lines.append("```\n")

        lines.append("Create files in these locations. Do NOT invent a different directory structure.\n")
        structure_section = "\n".join(lines)

    # --- Domain model section ---
    domain_model = spec.get("domain_model", {})
    domain_section = ""
    if domain_model:
        entities = domain_model.get("entities", [])
        roles = domain_model.get("roles", [])
        auth_model = domain_model.get("auth_model", {})

        lines = ["\n## Domain model\n"]

        if entities:
            lines.append("### Entities\n")
            for entity in entities:
                name = entity.get("name", "?")
                desc = entity.get("description", "")
                states = entity.get("states", [])
                lines.append(f"**{name}**: {desc}")
                if states:
                    lines.append(f"  States: {' → '.join(states)}")
                rels = entity.get("relationships", [])
                if rels:
                    lines.append(f"  Relationships: {', '.join(rels)}")
                lines.append("")

        if roles:
            lines.append("### Roles\n")
            for role in roles:
                name = role.get("name", "?")
                perms = role.get("can", [])
                lines.append(f"- **{name}**: {', '.join(perms)}")
            lines.append("")

        if auth_model:
            strategy = auth_model.get("strategy", "email_password")
            session = auth_model.get("session", "jwt")
            lines.append(f"### Auth: {strategy}, session: {session}\n")

        lines.append("Implement entities, states, and permissions as described above.\n")
        domain_section = "\n".join(lines)

    return f"""# AGENTS.md

## Project: {project_name}

{summary}

## Context

- App shape: {app_shape}
- Audience: {primary_audience}
- Surface: {surface}
- Stack: {stack.get("frontend", "?")} + {stack.get("backend", "?")} + {stack.get("database", "?")}
- Capabilities: {cap_text}
- Features: {feat_text}
- Core work features: {cwf_text}

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
- `.openclaw/api-contract.json` — shared frontend/backend contract for parallel loops
- `.openclaw/shared-plan.json`, `.openclaw/frontend-plan.json`, `.openclaw/backend-plan.json`, `.openclaw/integration-plan.json` — loop-specific plans
- `docs/stories/` — all story definitions

## Scope boundaries

{do_not_section}
- Do NOT redesign the architecture
- Do NOT add features not listed in the spec
- Do NOT skip to later stories — implement only what is asked
- Respect `.openclaw/api-contract.json` when a slice is running in `frontend`, `backend`, or `integration` mode
- Do NOT create files in `src/pages/` — this project uses the App Router (`src/app/`) exclusively
- Use environment variable names exactly as defined in `.env.example` — do NOT rename or invent alternatives (e.g. use `NEXT_PUBLIC_API_URL` not `NEXT_PUBLIC_API_BASE_URL`)
{structure_section}{domain_section}
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
2. Generate a migration: `{migration_create}`
3. Implement the migration (use `_pgm` as the parameter name to avoid lint warnings, e.g. `exports.up = (_pgm) => {{ ... }}`)
4. Run the migration: `{migration_cmd}`
5. Verify the migration ran: `{migration_status}`

**If you skip this step, the application will crash at runtime with "relation does not exist" errors.**

The ralph.sh script will also run `{migration_cmd}` after your story completes as a safety net, but you should generate the migration yourself as part of the story implementation.

## Validation

After implementing a story, run in this order (if available):

1. Generate and run migrations if schema changed: `{migration_cmd}`
2. `npm test` or equivalent test command
3. `npm run lint` or equivalent lint command
4. `npm run build` or equivalent build command

Record results. If a command doesn't exist yet, note that.

## Stack details

- Frontend: {stack.get("frontend", "unknown")}
- Backend: {stack.get("backend", "unknown")}
- Database: {stack.get("database", "unknown")}
- Deploy target: {answers.get("deploy_target", "unknown")}
- Migration command: `{migration_cmd}`
"""


def _build_ralph_sh(spec: dict[str, Any]) -> str:
    """Build ralph.sh — the story-by-story execution script for Codex CLI."""
    answers = spec.get("answers", {})
    project_name = answers.get("project_name", "Generated Project")
    migration_cmds = _detect_migration_commands(spec)
    migration_cmd = migration_cmds["run"]
    migration_create = migration_cmds["create"]
    migration_status = migration_cmds["status"]

    return f'''#!/usr/bin/env bash
set -euo pipefail

# ralph.sh — Parallel contract-first execution loop for {project_name}
# Usage: ./ralph.sh [--dry-run] [--from ST-XXX|FE-ST-XXX] [--track shared|frontend|backend|integration|all]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAN_FILE="$SCRIPT_DIR/.openclaw/execution-plan.json"
API_CONTRACT_FILE="$SCRIPT_DIR/.openclaw/api-contract.json"
SHARED_PLAN_FILE="$SCRIPT_DIR/.openclaw/shared-plan.json"
FRONTEND_PLAN_FILE="$SCRIPT_DIR/.openclaw/frontend-plan.json"
BACKEND_PLAN_FILE="$SCRIPT_DIR/.openclaw/backend-plan.json"
INTEGRATION_PLAN_FILE="$SCRIPT_DIR/.openclaw/integration-plan.json"
COMMANDS_FILE="$SCRIPT_DIR/.openclaw/commands.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
TRACK_PROGRESS_DIR="$SCRIPT_DIR/.openclaw/progress"
LOCKS_DIR="$SCRIPT_DIR/.openclaw/locks"
STORIES_DIR="$SCRIPT_DIR/docs/stories"
MIGRATION_CMD="{migration_cmd}"
MIGRATION_CREATE="{migration_create}"
MIGRATION_STATUS="{migration_status}"
CODEX_MODEL="${{CODEX_MODEL:-gpt-5.4}}"
CODEX_EFFORT="${{CODEX_EFFORT:-medium}}"
CODEX_RETRY_EFFORT="${{CODEX_RETRY_EFFORT:-low}}"

DRY_RUN=false
START_FROM=""
TRACK="all"
MAX_RETRIES=2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --from)
            START_FROM="$2"
            shift 2
            ;;
        --track)
            TRACK="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: ./ralph.sh [--dry-run] [--from ST-XXX|FE-ST-XXX] [--track shared|frontend|backend|integration|all]"
            exit 1
            ;;
    esac
done

if ! command -v jq &> /dev/null; then
    echo "Error: jq not found."
    echo "  apt-get install jq  OR  brew install jq"
    exit 1
fi

for required_file in "$PLAN_FILE" "$API_CONTRACT_FILE" "$SHARED_PLAN_FILE" "$FRONTEND_PLAN_FILE" "$BACKEND_PLAN_FILE" "$INTEGRATION_PLAN_FILE" "$COMMANDS_FILE"; do
    if [[ ! -f "$required_file" ]]; then
        echo "Error: required execution artifact not found: $required_file"
        echo "Run 'initializer prepare' first to regenerate the execution bundle."
        exit 1
    fi
done

mkdir -p "$TRACK_PROGRESS_DIR" "$LOCKS_DIR"
touch "$PROGRESS_FILE"

if [[ "$DRY_RUN" == false ]]; then
    if ! command -v npx &> /dev/null; then
        echo "Error: npx not found. Install Node.js first."
        exit 1
    fi
    if ! command -v codex &> /dev/null; then
        echo "Error: Codex CLI is not installed."
        echo ""
        echo "Install it with:"
        echo "  npm install -g @openai/codex"
        echo ""
        echo "Then log in with:"
        echo "  codex auth login"
        echo ""
        exit 1
    fi
    echo "Auth: OK (Codex CLI installed — uses your logged-in account)"
    echo ""
fi

TEST_CMD=$(jq -r '.commands.test // ""' "$COMMANDS_FILE")
LINT_CMD=$(jq -r '.commands.lint // ""' "$COMMANDS_FILE")
BUILD_CMD=$(jq -r '.commands.build // ""' "$COMMANDS_FILE")
TYPECHECK_CMD=$(jq -r '.commands.typecheck // ""' "$COMMANDS_FILE")
TEST_RUNNER=$(jq -r '.validation.test_runner // "none"' "$COMMANDS_FILE")
REQUIRES_REAL_TESTS=$(jq -r '.validation.requires_real_tests // false' "$COMMANDS_FILE")

track_progress_file() {{
    local track="$1"
    echo "$TRACK_PROGRESS_DIR/$track.txt"
}}

validation_policy_contains() {{
    local field="$1"
    local command_name="$2"
    jq -e --arg field "$field" --arg command_name "$command_name" \
        '.validation[$field] // [] | index($command_name)' \
        "$COMMANDS_FILE" >/dev/null 2>&1
}}

extract_error_loci() {{
    local output="$1"
    local loci=""

    # Extract file:line patterns from TypeScript/Next.js/ESLint output
    # Patterns: ./src/foo.ts(10,5), src/foo.ts:10:5, src/foo.ts(10), ./src/foo.tsx:10
    loci=$(echo "$output" | grep -oE '(\\.?/)?src/[^ :()]+[:(][0-9]+[,):]' | grep -v node_modules | grep -v '\\.next' | head -15 | sort -u)
    if [[ -z "$loci" ]]; then
        # Fallback: any file:line pattern
        loci=$(echo "$output" | grep -oE '[a-zA-Z0-9_./-]+\\.[a-z]+[:(][0-9]+[,):]' | grep -v node_modules | grep -v '\\.next' | head -15 | sort -u)
    fi

    echo "$loci"
}}

append_validation_error() {{
    local label="$1"
    local output="$2"
    local message
    local loci

    loci=$(extract_error_loci "$output")
    message="$label failure: $(echo "$output" | tail -10 | head -c 1500)"
    if [[ -n "$loci" ]]; then
        message="$message
Error loci:
$loci"
    fi
    if [[ -n "$VALIDATION_ERRORS" ]]; then
        VALIDATION_ERRORS="$VALIDATION_ERRORS | $message"
    else
        VALIDATION_ERRORS="$message"
    fi
}}

run_validation_command() {{
    local label="$1"
    local command="$2"
    local pretty="$3"
    local mode="$4"
    local output=""

    if [[ -z "$command" ]]; then
        echo "$pretty: SKIP"
        return 0
    fi

    if ! output=$(eval "$command" 2>&1); then
        echo "$pretty: FAIL"
        if [[ "$mode" == "block" ]] || ([[ "$mode" == "contract" ]] && validation_policy_contains "block_on" "$label"); then
            VALIDATION_OK=false
            append_validation_error "$pretty" "$output"
        fi
    else
        echo "$pretty: PASS"
    fi
}}

acquire_lock() {{
    local name="$1"
    local lock_dir="$LOCKS_DIR/$name.lock"
    while ! mkdir "$lock_dir" 2>/dev/null; do
        sleep 1
    done
    echo "$lock_dir"
}}

release_lock() {{
    local lock_dir="$1"
    if [[ -n "$lock_dir" ]] && [[ -d "$lock_dir" ]]; then
        rmdir "$lock_dir" 2>/dev/null || true
    fi
}}

append_progress() {{
    local track="$1"
    local unit_id="$2"
    local source_story_id="$3"
    local state="$4"
    local title="$5"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local line="[$timestamp] [$track] $unit_id ($source_story_id) — $state — $title"
    echo "$line" >> "$(track_progress_file "$track")"
    echo "$line" >> "$PROGRESS_FILE"
}}

track_has_start_token() {{
    local plan_file="$1"
    local token="$2"
    if [[ -z "$token" ]]; then
        return 1
    fi

    jq -e --arg token "$token" \
        '.stories[] | select(.id == $token or .source_story_id == $token)' \
        "$plan_file" >/dev/null 2>&1
}}

track_unit_done() {{
    local track="$1"
    local unit_id="$2"
    grep -q "$unit_id.*DONE" "$(track_progress_file "$track")" 2>/dev/null
}}

append_prompt_list() {{
    local plan_file="$1"
    local index="$2"
    local field="$3"
    local heading="$4"
    local prefix="$5"
    local items

    items=$(jq -r ".stories[$index].$field[]?" "$plan_file")
    if [[ -z "$items" ]]; then
        return 0
    fi

    printf '## %s\\n\\n' "$heading"
    while IFS= read -r item; do
        [[ -n "$item" ]] || continue
        printf '%s %s\\n' "$prefix" "$item"
    done <<< "$items"
    printf '\\n'
}}

enforce_owned_files() {{
    local plan_file="$1"
    local index="$2"
    local track="$3"
    local owned_files
    local changed_files
    local reverted=""

    owned_files=$(jq -r ".stories[$index].owned_files[]?" "$plan_file")
    if [[ -z "$owned_files" ]]; then
        return 0
    fi

    # Only check tracked files modified vs HEAD.  Untracked (new) files are
    # handled by the git-cat-file guard below — we never delete files that
    # don't exist in HEAD because they may belong to a parallel track.
    changed_files=$(cd "$SCRIPT_DIR" && git diff --name-only HEAD 2>/dev/null || true)
    if [[ -z "$changed_files" ]]; then
        return 0
    fi

    # Always allow derived artifacts and ralph-managed files that must not
    # be reverted even when a Codex slice touches them outside owned_files.
    # BUG-039: progress files and lock dirs are written by ralph.sh between
    # slices; reverting them breaks resume mode and crashes the pipeline.
    local always_allowed="package-lock.json progress.txt .openclaw/progress"

    while IFS= read -r changed; do
        [[ -n "$changed" ]] || continue
        # Skip always-allowed derived files (exact or prefix match)
        local skip_changed=false
        for allowed in $always_allowed; do
            if [[ "$changed" == "$allowed" ]] || [[ "$changed" == "$allowed"/* ]]; then
                skip_changed=true
                break
            fi
        done
        if [[ "$skip_changed" == true ]]; then
            continue
        fi
        local is_owned=false
        while IFS= read -r owned; do
            [[ -n "$owned" ]] || continue
            if [[ "$changed" == "$owned" ]] || [[ "$changed" == $owned/* ]]; then
                is_owned=true
                break
            fi
        done <<< "$owned_files"

        if [[ "$is_owned" == false ]]; then
            # BUG-041: In parallel tracks, another Codex may have created
            # files that don't belong to THIS track but DO belong to the
            # other.  Only revert files that exist in HEAD (restore original
            # version).  Files that are new (not in HEAD) were created by
            # either this Codex or a parallel one — leave them alone so the
            # owning track's enforcement and commit can handle them.
            if (cd "$SCRIPT_DIR" && git cat-file -e HEAD:"$changed" 2>/dev/null); then
                echo "  [$track] REVERT: $changed (not in owned_files)"
                (cd "$SCRIPT_DIR" && git checkout HEAD -- "$changed" 2>/dev/null || true)
                reverted="$reverted $changed"
            fi
        fi
    done <<< "$changed_files"

    if [[ -n "$reverted" ]]; then
        echo "  [$track] Owned-files enforcement reverted unauthorized changes"
    fi
}}

git_init_scaffold() {{
    if [[ -d "$SCRIPT_DIR/.git" ]]; then
        # Re-commit any scaffold changes from prepare regeneration (resume mode)
        if (cd "$SCRIPT_DIR" && ! git diff --quiet HEAD 2>/dev/null) || \
           (cd "$SCRIPT_DIR" && ! git diff --cached --quiet HEAD 2>/dev/null) || \
           [[ -n "$(cd "$SCRIPT_DIR" && git ls-files --others --exclude-standard)" ]]; then
            echo "Committing scaffold updates..."
            (cd "$SCRIPT_DIR" && git add -A && git commit -q -m "scaffold update")
        fi
        return 0
    fi
    echo "Initializing git repo for owned-files tracking..."
    (cd "$SCRIPT_DIR" && git init -q && git add -A && git commit -q -m "scaffold" --allow-empty)
}}

ensure_node_modules() {{
    if [[ -d "$SCRIPT_DIR/node_modules" ]]; then
        return 0
    fi
    echo "node_modules not found — installing dependencies..."
    if [[ -f "$SCRIPT_DIR/package-lock.json" ]]; then
        (cd "$SCRIPT_DIR" && npm ci)
    else
        (cd "$SCRIPT_DIR" && npm install)
    fi
    echo "Dependencies installed."
}}

lint_config_exists() {{
    [[ -f "$SCRIPT_DIR/eslint.config.mjs" ]] || \
    [[ -f "$SCRIPT_DIR/eslint.config.js" ]] || \
    [[ -f "$SCRIPT_DIR/.eslintrc.js" ]] || \
    [[ -f "$SCRIPT_DIR/.eslintrc.cjs" ]] || \
    [[ -f "$SCRIPT_DIR/.eslintrc.json" ]]
}}

bootstrap_scaffold_slice() {{
    local plan_file="$1"
    local index="$2"
    local source_story_key

    source_story_key=$(jq -r ".stories[$index].source_story_key // \\"\\"" "$plan_file")
    [[ "$source_story_key" == "bootstrap.repository" || "$source_story_key" == "bootstrap.repository-part-2" ]]
}}

owned_file_satisfied() {{
    local owned_file="$1"

    case "$owned_file" in
        ".eslintrc.js"|"eslint.config.js")
            lint_config_exists
            ;;
        *)
            [[ -f "$SCRIPT_DIR/$owned_file" ]]
            ;;
    esac
}}

bootstrap_scaffold_ready() {{
    local plan_file="$1"
    local index="$2"
    local owned_file=""

    if ! bootstrap_scaffold_slice "$plan_file" "$index"; then
        return 1
    fi

    while IFS= read -r owned_file; do
        [[ -n "$owned_file" ]] || continue
        if ! owned_file_satisfied "$owned_file"; then
            return 1
        fi
    done < <(jq -r ".stories[$index].owned_files[]?" "$plan_file")

    return 0
}}

append_bootstrap_prompt_guardrails() {{
    local plan_file="$1"
    local index="$2"

    if ! bootstrap_scaffold_slice "$plan_file" "$index"; then
        return 0
    fi

    cat <<'PROMPT_EOF'
## Bootstrap Guardrails

- This slice starts from the scaffold already generated by `initializer prepare`; audit the existing files before editing anything.
- If the existing scaffold already satisfies the story and validation passes, prefer leaving the files unchanged.
- Preserve working config files in place instead of rewriting them to match a preferred template.
- Treat `eslint.config.mjs`, `eslint.config.js`, and `.eslintrc.*` as equivalent lint config starting points; update the existing file instead of adding a duplicate.
- Do NOT rewrite `.env.local`.
- Do NOT modify files outside `Owned Files` unless a failing validation points directly to them.

PROMPT_EOF
}}

run_migrations() {{
    local track="$1"
    local needs_migrations="$2"
    local is_payload_backend=false
    local output=""

    if [[ "$needs_migrations" != "true" ]] || [[ "$track" == "frontend" ]]; then
        return 0
    fi

    if [[ ! -d "$SCRIPT_DIR/node_modules" ]]; then
        return 0
    fi

    if [[ ! -f "$SCRIPT_DIR/docker-compose.yml" ]] && [[ -z "${{DATABASE_URI:-}}" ]]; then
        return 0
    fi

    if [[ -f "$SCRIPT_DIR/src/payload.config.ts" ]] || [[ -f "$SCRIPT_DIR/payload.config.ts" ]]; then
        is_payload_backend=true
    fi

    if [[ "$MIGRATION_CMD" == "./node_modules/.bin/payload --disable-transpile migrate" ]] || [[ "$MIGRATION_CMD" == "payload --disable-transpile migrate" ]]; then
        if [[ ! -x "$SCRIPT_DIR/node_modules/.bin/payload" ]]; then
            return 0
        fi
        if [[ ! -f "$SCRIPT_DIR/src/payload.config.ts" ]] && [[ ! -f "$SCRIPT_DIR/payload.config.ts" ]]; then
            return 0
        fi
    elif [[ "$MIGRATION_CMD" == "npm run "* ]]; then
        local script_name="${{MIGRATION_CMD#npm run }}"
        if ! node -e "const p=require('./package.json'); if(!p.scripts?.['$script_name']) process.exit(1)" 2>/dev/null; then
            return 0
        fi
    fi

    echo "Running database migrations..."

    if command -v docker &> /dev/null && [[ -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
        if ! docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps --status running 2>/dev/null | grep -q postgres; then
            echo "  Starting database container..."
            docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d postgres 2>/dev/null || true
            for db_wait_attempt in $(seq 1 10); do
                if docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps --status running 2>/dev/null | grep -q postgres; then
                    break
                fi
                sleep 2
            done
        fi
    fi

    if output=$(eval "cd \\"$SCRIPT_DIR\\" && $MIGRATION_CMD" 2>&1); then
        if [[ "$is_payload_backend" == true ]] && printf '%s' "$output" | grep -q "__SPECWRIGHT_PAYLOAD_MIGRATIONS__:no-pending"; then
            echo "  Migrations: SKIP (no pending Payload migrations)"
        elif [[ "$is_payload_backend" == true ]] && printf '%s' "$output" | grep -q "__SPECWRIGHT_PAYLOAD_MIGRATIONS__:dev-push"; then
            echo "  Migrations: WARN (skipped Payload migrate: dev-mode push marker found in payload_migrations)"
        else
            echo "  Migrations: OK"
        fi
    else
        echo "  Migrations: WARN (command failed, may need manual intervention)"
    fi
}}

run_track_validation() {{
    local track="$1"
    local validation_mode="$2"

    VALIDATION_OK=true
    VALIDATION_ERRORS=""
    echo "Running validation..."

    # NOTE: Do NOT delete .next here.  Removing it while a parallel Codex
    # process may be writing build artifacts causes clientReferenceManifest
    # races.  `next build` already does a full recompile from source files;
    # stale .next cache does not cause corruption on its own.

    # Build runs FIRST so that .next artifacts exist for tests that import
    # Server Components (avoids clientReferenceManifest errors after rm -rf .next).
    if [[ "$validation_mode" == "partial" ]]; then
        run_validation_command "build" "$BUILD_CMD" "Build" "block"
        # Skip typecheck when build failed — .next/types/ won't exist (BUG-032)
        if [[ "$VALIDATION_OK" == true ]]; then
            # BUG-037: remove stale tsbuildinfo so incremental tsc doesn't
            # reference .next/types/ entries from a previous build.
            rm -f tsconfig.tsbuildinfo
            # BUG-037b: .next/types/ may not exist even after a successful build
            # (e.g. first build for a track, or partial Next.js output).  Running
            # typecheck with tsconfig including '.next/types/**/*.ts' will fail
            # with TS6053.  Skip typecheck when the directory is absent.
            if [[ -d .next/types ]]; then
                run_validation_command "typecheck" "$TYPECHECK_CMD" "Typecheck" "block"
            else
                echo "Typecheck: SKIP (.next/types/ not found — build did not generate type stubs)"
            fi
        fi
        run_validation_command "lint" "$LINT_CMD" "Lint" "warn"
        run_validation_command "test" "$TEST_CMD" "Tests" "warn"
        return 0
    fi

    run_validation_command "build" "$BUILD_CMD" "Build" "contract"
    # Skip typecheck when build failed — .next/types/ won't exist (BUG-032)
    if [[ "$VALIDATION_OK" == true ]]; then
        # BUG-037: remove stale tsbuildinfo so incremental tsc doesn't
        # reference .next/types/ entries from a previous build.
        rm -f tsconfig.tsbuildinfo
        # BUG-037b: skip typecheck when .next/types/ was not generated
        if [[ -d .next/types ]]; then
            run_validation_command "typecheck" "$TYPECHECK_CMD" "Typecheck" "contract"
        else
            echo "Typecheck: SKIP (.next/types/ not found — build did not generate type stubs)"
        fi
    fi
    run_validation_command "lint" "$LINT_CMD" "Lint" "contract"

    if [[ "$REQUIRES_REAL_TESTS" == "true" ]] && validation_policy_contains "block_on" "test"; then
        if [[ -z "$TEST_CMD" ]] || [[ "$TEST_RUNNER" == "none" ]]; then
            echo "Tests: FAIL"
            VALIDATION_OK=false
            append_validation_error "Tests" "No real test runner is configured in .openclaw/commands.json"
        else
            run_validation_command "test" "$TEST_CMD" "Tests" "contract"
        fi
    else
        run_validation_command "test" "$TEST_CMD" "Tests" "contract"
    fi
}}

run_codex_unit() {{
    local track="$1"
    local plan_file="$2"
    local index="$3"
    local prompt_file
    local output_file
    local unit_id
    local source_story_id
    local unit_title
    local source_story_title
    local validation_mode
    local contract_domains

    unit_id=$(jq -r ".stories[$index].id" "$plan_file")
    source_story_id=$(jq -r ".stories[$index].source_story_id" "$plan_file")
    unit_title=$(jq -r ".stories[$index].title" "$plan_file")
    source_story_title=$(jq -r ".stories[$index].source_story_title" "$plan_file")
    validation_mode=$(jq -r ".stories[$index].validation_mode // \\"full\\"" "$plan_file")
    contract_domains=$(jq -r ".stories[$index].contract_domains | join(\\", \\")" "$plan_file")

    prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
    output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

    {{
        printf '# Task: Implement %s — %s\\n\\n' "$unit_id" "$unit_title"
        cat <<'PROMPT_EOF'
You are implementing a single execution slice for the project **{project_name}**.

PROMPT_EOF
        printf -- '- Track: `%s`\\n' "$track"
        printf -- '- Source story: `%s`\\n' "$source_story_id"
        printf -- '- Shared contract: `.openclaw/api-contract.json`\\n'
        if [[ -n "$contract_domains" ]]; then
            printf -- '- Contract domains: `%s`\\n' "$contract_domains"
        fi
        printf -- '- Validation mode: `%s`\\n\\n' "$validation_mode"
        append_prompt_list "$plan_file" "$index" "owned_files" "Owned Files" "- "
        append_prompt_list "$plan_file" "$index" "prompt_rules" "Track Rules" "- "
        append_bootstrap_prompt_guardrails "$plan_file" "$index"
        cat <<'PROMPT_EOF'
## Source Story

PROMPT_EOF
        if [[ -f "$STORIES_DIR/$source_story_id.md" ]]; then
            cat "$STORIES_DIR/$source_story_id.md"
        else
            printf 'Implement: %s\\n' "$source_story_title"
        fi
        printf '\\n\\n'
        cat <<'PROMPT_EOF'
## Instructions

- Read `.codex/AGENTS.md` for project-wide context
- Read `.openclaw/api-contract.json` before changing any contract-bound behavior
- Read `spec.json` and `architecture.md` if the slice needs more context
- Make minimal, targeted changes for this slice only
- Do not change unrelated tracks or rewrite the architecture
- Record any targeted checks you ran in your response
- Do NOT proactively run repo-wide validation or shared-runtime commands (`npm run build`, `npm run lint`, `npm test`, `npm run typecheck`, `npm run db:migrate*`, `docker compose ...`) during the Codex step
- `ralph.sh` will run serialized migrations and official validation for this slice after Codex exits
- If the source story lists manual validation outside this slice's owned files or track, leave that for the runner or a later slice instead of forcing it here

## CRITICAL: Database Migrations

If this slice changes schema, collections, models, or database structure:

PROMPT_EOF
        printf '1. Generate a migration: `%s`\\n' "$MIGRATION_CREATE"
        printf '2. Run the migration: `%s`\\n' "$MIGRATION_CMD"
        printf '3. Verify with: `%s`\\n\\n' "$MIGRATION_STATUS"
        cat <<'PROMPT_EOF'
## Validation

- `ralph.sh` will run migrations and the official validation for this slice after Codex exits.
- If you need extra confidence while editing, prefer the narrowest non-conflicting check possible.
- Avoid commands that mutate shared build artifacts or shared runtime state unless you are debugging a concrete failure from this attempt.
PROMPT_EOF
    }} > "$prompt_file"

    codex exec \\
        --model "$CODEX_MODEL" \\
        --config "model_reasoning_effort=\\"$CODEX_EFFORT\\"" \\
        --sandbox danger-full-access \\
        --json \\
        --output-last-message "$output_file" \\
        - < "$prompt_file"

    local exit_code=$?
    if [[ -f "$output_file" ]]; then
        local output_content
        output_content=$(cat "$output_file")
        if [[ -z "$output_content" ]] || [[ "$output_content" == *'"type":"error"'* ]]; then
            echo "Codex returned empty or error output for $unit_id"
            rm -f "$prompt_file" "$output_file"
            return 1
        fi
        echo "$output_content"
    else
        echo "No output file generated for $unit_id"
        rm -f "$prompt_file" "$output_file"
        return 1
    fi

    rm -f "$prompt_file" "$output_file"
    return $exit_code
}}

run_codex_retry_unit() {{
    local track="$1"
    local plan_file="$2"
    local index="$3"
    local previous_error="$4"
    local prompt_file
    local output_file
    local unit_id
    local source_story_id
    local unit_title
    local source_story_title

    unit_id=$(jq -r ".stories[$index].id" "$plan_file")
    source_story_id=$(jq -r ".stories[$index].source_story_id" "$plan_file")
    unit_title=$(jq -r ".stories[$index].title" "$plan_file")
    source_story_title=$(jq -r ".stories[$index].source_story_title" "$plan_file")

    prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
    output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

    {{
        printf '# RETRY: Fix %s — %s\\n\\n' "$unit_id" "$unit_title"
        cat <<'PROMPT_EOF'
You are RETRYING a slice that failed on the previous attempt for the project **{project_name}**.

## Previous Error

The previous attempt failed with:

PROMPT_EOF
        printf '```\\n%s\\n```\\n\\n' "$previous_error"
        local retry_loci
        retry_loci=$(extract_error_loci "$previous_error")
        if [[ -n "$retry_loci" ]]; then
            printf '## Error Locations\\n\\nThe following files/lines had errors — start here:\\n\\n'
            while IFS= read -r locus; do
                [[ -n "$locus" ]] || continue
                printf -- '- `%s`\\n' "$locus"
            done <<< "$retry_loci"
            printf '\\nOpen these files first and fix the specific errors before doing anything else.\\n\\n'
        fi
        append_prompt_list "$plan_file" "$index" "prompt_rules" "Track Rules" "- "
        append_bootstrap_prompt_guardrails "$plan_file" "$index"
        printf '## Source Story\\n\\nRefer to `docs/stories/%s.md` (unchanged from first attempt).\\n\\n' "$source_story_id"
        cat <<'PROMPT_EOF'
## What to do

1. Read the error above carefully
2. Fix only the issue that blocked the slice
3. Preserve the shared contract and track ownership boundaries
4. Do NOT proactively rerun repo-wide validation or shared-runtime commands (`npm run build`, `npm run lint`, `npm test`, `npm run typecheck`, `npm run db:migrate*`, `docker compose ...`) unless the previous error requires a targeted repro
5. Let `ralph.sh` rerun serialized migrations and official validation after you finish

## CRITICAL: Database Migrations

If the error is about missing tables or columns ("relation does not exist"):
PROMPT_EOF
        printf '1. Generate a migration: `%s`\\n' "$MIGRATION_CREATE"
        printf '2. Run the migration: `%s`\\n\\n' "$MIGRATION_CMD"
        cat <<'PROMPT_EOF'
## Validation

After fixing, prefer the smallest targeted repro only when needed. `ralph.sh` will rerun migrations, build, typecheck, lint, and tests as applicable after Codex exits.
PROMPT_EOF
    }} > "$prompt_file"

    codex exec \\
        --model "$CODEX_MODEL" \\
        --config "model_reasoning_effort=\\"$CODEX_RETRY_EFFORT\\"" \\
        --sandbox danger-full-access \\
        --json \\
        --output-last-message "$output_file" \\
        - < "$prompt_file"

    local exit_code=$?
    if [[ -f "$output_file" ]]; then
        local output_content
        output_content=$(cat "$output_file")
        if [[ -z "$output_content" ]] || [[ "$output_content" == *'"type":"error"'* ]]; then
            echo "Codex returned empty or error output for $unit_id (retry)"
            rm -f "$prompt_file" "$output_file"
            return 1
        fi
        echo "$output_content"
    else
        echo "No output file generated for $unit_id (retry)"
        rm -f "$prompt_file" "$output_file"
        return 1
    fi

    rm -f "$prompt_file" "$output_file"
    return $exit_code
}}

run_track_plan() {{
    local track="$1"
    local plan_file="$2"
    local start_token="$3"
    local total
    local started=true
    local failed=0
    local track_label

    total=$(jq '.total_stories' "$plan_file")
    track_label=$(jq -r '.label // "Track"' "$plan_file")

    if [[ "$total" -eq 0 ]]; then
        echo "[$track] No stories in plan."
        return 0
    fi

    if [[ -n "$start_token" ]] && track_has_start_token "$plan_file" "$start_token"; then
        started=false
    fi

    echo ""
    echo "=== $track_label Loop ==="
    echo "Stories: $total"
    echo "Plan: $plan_file"
    echo ""

    for i in $(seq 0 $(( total - 1 ))); do
        local unit_id
        local source_story_id
        local unit_title
        local unit_phase
        local unit_order
        local validation_mode
        local needs_migrations

        unit_id=$(jq -r ".stories[$i].id" "$plan_file")
        source_story_id=$(jq -r ".stories[$i].source_story_id" "$plan_file")
        unit_title=$(jq -r ".stories[$i].title" "$plan_file")
        unit_phase=$(jq -r ".stories[$i].phase" "$plan_file")
        unit_order=$(jq -r ".stories[$i].order" "$plan_file")
        validation_mode=$(jq -r ".stories[$i].validation_mode // \\"full\\"" "$plan_file")
        needs_migrations=$(jq -r ".stories[$i].needs_migrations // false" "$plan_file")

        if [[ "$started" == false ]]; then
            if [[ "$unit_id" == "$start_token" ]] || [[ "$source_story_id" == "$start_token" ]]; then
                started=true
            else
                continue
            fi
        fi

        if track_unit_done "$track" "$unit_id"; then
            echo "[$track $unit_order/$total] $unit_id — SKIP (already done)"
            continue
        fi

        echo "---"
        echo "[$track $unit_order/$total] $unit_id — $unit_title"
        echo "Source story: $source_story_id"
        echo "Phase: $unit_phase"
        echo ""

        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY RUN] Would run codex with:"
            echo "  Track: $track"
            echo "  Unit: $unit_id"
            echo "  Source story: $source_story_id"
            echo ""
            continue
        fi

        append_progress "$track" "$unit_id" "$source_story_id" "START" "$unit_title"

        # BUG-036: Auto-skip slices with no owned files — nothing to implement in this track
        local owned_count
        owned_count=$(jq -r ".stories[$i].owned_files | length" "$plan_file")
        if [[ "$owned_count" -eq 0 ]]; then
            echo "[$track $unit_order/$total] $unit_id — SKIP (no owned files for this track)"
            append_progress "$track" "$unit_id" "$source_story_id" "DONE" "$unit_title (no owned files — auto-skip)"
            continue
        fi

        if bootstrap_scaffold_ready "$plan_file" "$i"; then
            echo "Bootstrap scaffold already exists for $unit_id. Validating before invoking Codex..."
            local validation_lock=""
            validation_lock=$(acquire_lock "validation")
            run_track_validation "$track" "$validation_mode"
            release_lock "$validation_lock"

            if [[ "$VALIDATION_OK" == true ]]; then
                append_progress "$track" "$unit_id" "$source_story_id" "DONE" "$unit_title (scaffold already satisfied)"

                echo "[$track $unit_order/$total] $unit_id — DONE (scaffold already satisfied)"
                # Commit scaffold state so next git diff is scoped correctly
                local git_lock=""
                git_lock=$(acquire_lock "git")
                (cd "$SCRIPT_DIR" && git add -A && git commit -q -m "slice: $unit_id (scaffold skip)" --allow-empty 2>/dev/null || true)
                release_lock "$git_lock"
                continue
            fi

            echo "Bootstrap scaffold preflight failed for $unit_id. Falling back to Codex..."
        fi

        local slice_done=false
        local attempt=0
        local last_error=""

        while [[ "$slice_done" == false ]] && [[ $attempt -le $MAX_RETRIES ]]; do
            attempt=$((attempt + 1))

            if [[ $attempt -gt 1 ]]; then
                echo "  Retry $((attempt - 1))/$MAX_RETRIES for $unit_id..."
                append_progress "$track" "$unit_id" "$source_story_id" "RETRY" "Attempt $attempt: $last_error"
                sleep 1
            fi

            local codex_ok=""
            if [[ $attempt -eq 1 ]]; then
                if run_codex_unit "$track" "$plan_file" "$i"; then
                    codex_ok="ok"
                fi
            else
                if run_codex_retry_unit "$track" "$plan_file" "$i" "$last_error"; then
                    codex_ok="ok"
                fi
            fi

            if [[ -z "$codex_ok" ]]; then
                last_error="Codex execution failed"
                echo "  Codex failed (attempt $attempt)"

                if [[ $attempt -gt $MAX_RETRIES ]]; then
                    append_progress "$track" "$unit_id" "$source_story_id" "BLOCKED" "Codex failed after $attempt attempts"
                    failed=$((failed + 1))
                    break
                fi
                continue
            fi

            enforce_owned_files "$plan_file" "$i" "$track"

            local migration_lock=""
            migration_lock=$(acquire_lock "migrations")
            run_migrations "$track" "$needs_migrations"
            release_lock "$migration_lock"

            if [[ "$validation_mode" == "partial" ]]; then
                # Partial mode: only lock around build (writes to shared .next/).
                # Typecheck/lint/test are read-only and can overlap across tracks.
                VALIDATION_OK=true
                VALIDATION_ERRORS=""
                local build_lock=""
                build_lock=$(acquire_lock "validation")
                run_validation_command "build" "$BUILD_CMD" "Build" "block"
                release_lock "$build_lock"
                # Skip typecheck when build failed — .next/types/ won't exist (BUG-032)
                if [[ "$VALIDATION_OK" == true ]]; then
                    # BUG-037: remove stale tsbuildinfo so incremental tsc doesn't
                    # reference .next/types/ entries from a previous build.
                    rm -f tsconfig.tsbuildinfo
                    # BUG-037b: skip typecheck when .next/types/ was not generated
                    if [[ -d .next/types ]]; then
                        run_validation_command "typecheck" "$TYPECHECK_CMD" "Typecheck" "block"
                    else
                        echo "Typecheck: SKIP (.next/types/ not found — build did not generate type stubs)"
                    fi
                fi
                # Scoped lint: only lint owned files instead of entire project
                local owned_lint_files
                owned_lint_files=$(jq -r ".stories[$i].owned_files[]" "$plan_file" 2>/dev/null \\
                    | grep -E '\\.(ts|tsx|js|jsx)$' \\
                    | tr '\\n' ' ')
                if [[ -n "$owned_lint_files" ]]; then
                    run_validation_command "lint" "npx eslint $owned_lint_files" "Lint" "warn"
                else
                    run_validation_command "lint" "$LINT_CMD" "Lint" "warn"
                fi
                run_validation_command "test" "$TEST_CMD" "Tests" "warn"
            else
                local validation_lock=""
                validation_lock=$(acquire_lock "validation")
                run_track_validation "$track" "$validation_mode"
                release_lock "$validation_lock"
            fi

            if [[ "$VALIDATION_OK" == true ]]; then
                if [[ $attempt -gt 1 ]]; then
                    append_progress "$track" "$unit_id" "$source_story_id" "DONE" "$unit_title (succeeded on attempt $attempt)"
                else
                    append_progress "$track" "$unit_id" "$source_story_id" "DONE" "$unit_title"
                fi
                echo "[$track $unit_order/$total] $unit_id — DONE"
                slice_done=true
                # Commit slice changes so next git diff is scoped to next slice only
                local git_lock=""
                git_lock=$(acquire_lock "git")
                (cd "$SCRIPT_DIR" && git add -A && git commit -q -m "slice: $unit_id" --allow-empty 2>/dev/null || true)
                release_lock "$git_lock"
            else
                last_error="$VALIDATION_ERRORS"
                echo "  Validation failed (attempt $attempt)"

                if [[ $attempt -gt $MAX_RETRIES ]]; then
                    append_progress "$track" "$unit_id" "$source_story_id" "VALIDATION" "Failed after $attempt attempts: $VALIDATION_ERRORS"
                    failed=$((failed + 1))
                fi
            fi
        done
    done

    if [[ $failed -gt 0 ]]; then
        return 1
    fi

    return 0
}}

TOTAL=$(jq '.total_stories' "$PLAN_FILE")
git_init_scaffold
ensure_node_modules
echo ""
echo "=== Ralph Loop: {project_name} ==="
echo "Stories: $TOTAL"
echo "Project: $SCRIPT_DIR"
echo "Strategy: $(jq -r '.parallel_execution.strategy // "serial"' "$PLAN_FILE")"
echo ""

FAILURES=0

if [[ "$TRACK" == "shared" ]]; then
    run_track_plan "shared" "$SHARED_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
elif [[ "$TRACK" == "frontend" ]]; then
    run_track_plan "frontend" "$FRONTEND_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
elif [[ "$TRACK" == "backend" ]]; then
    run_track_plan "backend" "$BACKEND_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
elif [[ "$TRACK" == "integration" ]]; then
    run_track_plan "integration" "$INTEGRATION_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
else
    run_track_plan "shared" "$SHARED_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))

    if [[ $FAILURES -eq 0 ]]; then
        if [[ "${{PARALLEL_TRACKS:-false}}" == "true" ]]; then
            # Parallel mode (opt-in via PARALLEL_TRACKS=true)
            frontend_failed=0
            backend_failed=0

            run_track_plan "frontend" "$FRONTEND_PLAN_FILE" "$START_FROM" &
            FRONTEND_PID=$!
            run_track_plan "backend" "$BACKEND_PLAN_FILE" "$START_FROM" &
            BACKEND_PID=$!

            wait "$FRONTEND_PID" || frontend_failed=1
            wait "$BACKEND_PID" || backend_failed=1

            FAILURES=$((FAILURES + frontend_failed + backend_failed))
        else
            # Sequential mode (default): backend first, then frontend
            # Both tracks always run — blocked slices in one track should
            # not prevent the other from executing.
            run_track_plan "backend" "$BACKEND_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
            run_track_plan "frontend" "$FRONTEND_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
        fi
    fi

    if [[ $FAILURES -eq 0 ]]; then
        echo ""
        echo "=== Integration Gate: cross-track validation ==="

        # Start database for integration validation (SSG pages may need DB)
        if command -v docker &>/dev/null && [[ -f docker-compose.yml ]]; then
            echo "Starting database for integration validation..."
            docker compose up -d postgres 2>/dev/null || true
            for db_gate_attempt in $(seq 1 15); do
                if docker compose exec -T postgres pg_isready -U postgres &>/dev/null; then
                    echo "Database ready."
                    break
                fi
                sleep 2
            done
        fi

        VALIDATION_OK=true
        VALIDATION_ERRORS=""
        run_track_validation "integration-gate" "full"
        if [[ "$VALIDATION_OK" != true ]]; then
            echo "Integration gate FAILED: $VALIDATION_ERRORS"
            echo "Skipping integration track."
            FAILURES=$((FAILURES + 1))
        else
            echo "Integration gate PASSED"
            run_track_plan "integration" "$INTEGRATION_PLAN_FILE" "$START_FROM" || FAILURES=$((FAILURES + 1))
        fi
    fi
fi

IMPLEMENTED=$( (grep -h "DONE" "$TRACK_PROGRESS_DIR"/*.txt 2>/dev/null || true) | wc -l | tr -d ' ' )
echo ""
echo "=== Ralph Loop Complete ==="
echo "Implemented slices: $IMPLEMENTED"
echo "Failed tracks: $FAILURES"
echo "Total source stories: $TOTAL"
echo ""

if [[ $FAILURES -gt 0 ]]; then
    exit 1
fi
'''


def write_codex_bundle(output_dir: Path, spec: dict[str, Any]) -> None:
    """Generate .codex/AGENTS.md and ralph.sh for the Codex CLI."""

    # .codex/AGENTS.md — Codex CLI reads this automatically
    codex_dir = output_dir / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)

    agents_path = codex_dir / "AGENTS.md"
    agents_path.write_text(_build_agents_md(spec), encoding="utf-8")

    # ralph.sh at root — the execution loop
    ralph_path = output_dir / "ralph.sh"
    ralph_path.write_text(_build_ralph_sh(spec), encoding="utf-8")

    # Make ralph.sh executable
    ralph_path.chmod(ralph_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
