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
    backend = (spec.get("stack", {}).get("backend") or "").lower().strip()

    if backend in ("payload", "payload-cms"):
        return {
            "run": "npx payload migrate",
            "create": "npx payload migrate:create",
            "status": "npx payload migrate:status",
        }
    elif backend == "django":
        return {
            "run": "python manage.py migrate",
            "create": "python manage.py makemigrations",
            "status": "python manage.py showmigrations",
        }
    else:
        return {
            "run": "npm run db:migrate",
            "create": "npm run db:migrate:create",
            "status": "npm run db:migrate:status",
        }


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
- `docs/stories/` — all story definitions

## Scope boundaries

{do_not_section}
- Do NOT redesign the architecture
- Do NOT add features not listed in the spec
- Do NOT skip to later stories — implement only what is asked
- Do NOT create files in `src/pages/` — this project uses the App Router (`src/app/`) exclusively
- Use environment variable names exactly as defined in `.env.example` — do NOT rename or invent alternatives (e.g. use `NEXT_PUBLIC_API_URL` not `NEXT_PUBLIC_API_BASE_URL`)
{structure_section}{domain_section}
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

# ralph.sh — Story-by-story execution loop for {project_name}
# Usage: ./ralph.sh [--dry-run] [--from ST-XXX]
#
# This script reads .openclaw/execution-plan.json, finds the next
# pending story, builds a prompt file, and runs Codex CLI to implement it.
# After each story, it runs migrations and validation, then records progress.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAN_FILE="$SCRIPT_DIR/.openclaw/execution-plan.json"
COMMANDS_FILE="$SCRIPT_DIR/.openclaw/commands.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
STORIES_DIR="$SCRIPT_DIR/docs/stories"
MIGRATION_CMD="{migration_cmd}"
MIGRATION_CREATE="{migration_create}"
MIGRATION_STATUS="{migration_status}"
CODEX_MODEL="${{CODEX_MODEL:-gpt-5.4}}"

DRY_RUN=false
START_FROM=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --from)
            START_FROM="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: ./ralph.sh [--dry-run] [--from ST-XXX]"
            exit 1
            ;;
    esac
done

# -------------------------------------------------------
# Dependency checks
# -------------------------------------------------------

if ! command -v npx &> /dev/null; then
    echo "Error: npx not found. Install Node.js first."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq not found."
    echo "  apt-get install jq  OR  brew install jq"
    exit 1
fi

if [[ ! -f "$PLAN_FILE" ]]; then
    echo "Error: execution-plan.json not found at $PLAN_FILE"
    echo "Run 'initializer new' first to generate the project."
    exit 1
fi

if [[ ! -f "$COMMANDS_FILE" ]]; then
    echo "Error: commands.json not found at $COMMANDS_FILE"
    echo "Run 'initializer prepare' first to generate the execution bundle."
    exit 1
fi

# -------------------------------------------------------
# Auth check
# -------------------------------------------------------

if [[ "$DRY_RUN" == false ]]; then
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

validation_policy_contains() {{
    local field="$1"
    local command_name="$2"
    jq -e --arg field "$field" --arg command_name "$command_name" \
        '.validation[$field] // [] | index($command_name)' \
        "$COMMANDS_FILE" >/dev/null 2>&1
}}

append_validation_error() {{
    local label="$1"
    local output="$2"
    local message

    message="$label failure: $(echo "$output" | tail -20)"
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
    local output=""

    if [[ -z "$command" ]]; then
        echo "$pretty: SKIP"
        return 0
    fi

    if ! output=$(eval "$command" 2>&1); then
        echo "$pretty: FAIL"
        if validation_policy_contains "block_on" "$label"; then
            VALIDATION_OK=false
            append_validation_error "$pretty" "$output"
        fi
    else
        echo "$pretty: PASS"
    fi
}}

# -------------------------------------------------------
# Migration runner
# -------------------------------------------------------

run_migrations() {{
    # Only run if node_modules exists (project has been installed)
    if [[ ! -d "$SCRIPT_DIR/node_modules" ]]; then
        return 0
    fi

    # Only run if there's a database configured
    if [[ ! -f "$SCRIPT_DIR/docker-compose.yml" ]] && [[ -z "${{DATABASE_URI:-}}" ]]; then
        return 0
    fi

    # Only run if the migration command is available
    # For payload: check if payload is installed
    # For npm scripts: check if the script exists in package.json
    if [[ "$MIGRATION_CMD" == "npx payload migrate" ]]; then
        # Check if payload is installed
        if [[ ! -f "$SCRIPT_DIR/node_modules/.package-lock.json" ]] && ! npx payload --help &>/dev/null; then
            return 0
        fi
        # Check if payload config exists (means backend is set up)
        if [[ ! -f "$SCRIPT_DIR/src/payload.config.ts" ]] && [[ ! -f "$SCRIPT_DIR/payload.config.ts" ]]; then
            return 0
        fi
    elif [[ "$MIGRATION_CMD" == "npm run "* ]]; then
        # Extract script name from "npm run db:migrate"
        local script_name="${{MIGRATION_CMD#npm run }}"
        if ! node -e "const p=require('./package.json'); if(!p.scripts?.['$script_name']) process.exit(1)" 2>/dev/null; then
            return 0
        fi
    fi

    echo "Running database migrations..."

    # Check if database is reachable before running migrations
    if command -v docker &> /dev/null && [[ -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
        # Ensure database container is running
        if ! docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps --status running 2>/dev/null | grep -q postgres; then
            echo "  Starting database container..."
            docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d postgres 2>/dev/null || true
            # Wait for health check
            for attempt in $(seq 1 10); do
                if docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps --status running 2>/dev/null | grep -q postgres; then
                    break
                fi
                sleep 2
            done
        fi
    fi

    # Run the migration command
    if eval "cd \\"$SCRIPT_DIR\\" && $MIGRATION_CMD" 2>&1; then
        echo "  Migrations: OK"
    else
        echo "  Migrations: WARN (command failed, may need manual intervention)"
        # Don't fail the story — the agent may not have created new migrations
    fi
}}

# -------------------------------------------------------
# Codex runner
# -------------------------------------------------------

run_codex() {{
    local story_id="$1"
    local story_title="$2"
    local prompt_file
    local output_file

    prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
    output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

    _cleanup() {{
        rm -f "$prompt_file" "$output_file"
    }}
    trap _cleanup RETURN

    # Build prompt file
    cat > "$prompt_file" <<PROMPT_EOF
# Task: Implement $story_id — $story_title

You are implementing a single story for the project **{project_name}**.

## Story

$(if [[ -f "$STORIES_DIR/$story_id.md" ]]; then cat "$STORIES_DIR/$story_id.md"; else echo "Implement: $story_title"; fi)

## Instructions

- Read .codex/AGENTS.md for project context and scope boundaries
- Read spec.json for the full project specification
- Read architecture.md for component structure
- Make minimal, targeted changes for this story ONLY
- Do NOT change architecture or scope beyond what this story requires
- Run tests if available after implementation
- If this is a bootstrap story, set up the project structure first

## CRITICAL: Database Migrations

If this story adds, removes, or modifies any collection fields, database models, 
or schema (including adding localization to fields), you MUST:

1. Make the schema change
2. Generate a migration: `$MIGRATION_CREATE`
3. Run the migration: `$MIGRATION_CMD`
4. Verify with: `$MIGRATION_STATUS`

Skipping this will cause runtime errors like "relation does not exist".

## Validation

After implementation, run available validation commands (test, lint, build).
If no commands exist yet, note that in your response.
PROMPT_EOF

    # Run Codex via installed CLI
    codex exec \\
        --model "$CODEX_MODEL" \\
        --config 'model_reasoning_effort="xhigh"' \\
        --sandbox danger-full-access \\
        --json \\
        --output-last-message "$output_file" \\
        - < "$prompt_file"

    local exit_code=$?

    if [[ -f "$output_file" ]]; then
        local output_content
        output_content=$(cat "$output_file")

        # Check if output is empty or contains error
        if [[ -z "$output_content" ]] || [[ "$output_content" == *'"type":"error"'* ]]; then
            echo "Codex returned empty or error output for $story_id"
            return 1
        fi

        echo "$output_content"
    else
        echo "No output file generated for $story_id"
        return 1
    fi

    return $exit_code
}}

# -------------------------------------------------------
# Codex retry runner (includes error context)
# -------------------------------------------------------

run_codex_retry() {{
    local story_id="$1"
    local story_title="$2"
    local previous_error="$3"
    local prompt_file
    local output_file

    prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
    output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

    _cleanup() {{
        rm -f "$prompt_file" "$output_file"
    }}
    trap _cleanup RETURN

    # Build retry prompt with error context
    cat > "$prompt_file" <<PROMPT_EOF
# RETRY: Fix $story_id — $story_title

You are RETRYING a story that failed on the previous attempt for the project **{project_name}**.

## Previous Error

The previous attempt failed with:

\\`\\`\\`
$previous_error
\\`\\`\\`

## What to do

1. Read the error above carefully
2. Identify what went wrong (build error, missing migration, type error, test failure)
3. Fix ONLY the issue described — do not rewrite the entire story
4. Run validation to confirm the fix works

## Story

$(if [[ -f "$STORIES_DIR/$story_id.md" ]]; then cat "$STORIES_DIR/$story_id.md"; else echo "Implement: $story_title"; fi)

## CRITICAL: Database Migrations

If the error is about missing tables or columns ("relation does not exist"):
1. Generate a migration: `$MIGRATION_CREATE`
2. Run the migration: `$MIGRATION_CMD`

## Validation

After fixing, run: test, lint, build.
PROMPT_EOF

    # Run Codex via installed CLI
    codex exec \\
        --model "$CODEX_MODEL" \\
        --config 'model_reasoning_effort="xhigh"' \\
        --sandbox danger-full-access \\
        --json \\
        --output-last-message "$output_file" \\
        - < "$prompt_file"

    local exit_code=$?

    if [[ -f "$output_file" ]]; then
        local output_content
        output_content=$(cat "$output_file")

        if [[ -z "$output_content" ]] || [[ "$output_content" == *'"type":"error"'* ]]; then
            echo "Codex returned empty or error output for $story_id (retry)"
            return 1
        fi

        echo "$output_content"
    else
        echo "No output file generated for $story_id (retry)"
        return 1
    fi

    return $exit_code
}}

# -------------------------------------------------------
# Read execution plan
# -------------------------------------------------------

TOTAL=$(jq '.total_stories' "$PLAN_FILE")
echo ""
echo "=== Ralph Loop: {project_name} ==="
echo "Stories: $TOTAL"
echo "Project: $SCRIPT_DIR"
echo ""

STARTED=false
if [[ -z "$START_FROM" ]]; then
    STARTED=true
fi

IMPLEMENTED=0
FAILED=0
MAX_RETRIES=2

for i in $(seq 0 $(( TOTAL - 1 ))); do
    STORY_ID=$(jq -r ".stories[$i].id" "$PLAN_FILE")
    STORY_TITLE=$(jq -r ".stories[$i].title" "$PLAN_FILE")
    STORY_PHASE=$(jq -r ".stories[$i].phase" "$PLAN_FILE")
    STORY_ORDER=$(jq -r ".stories[$i].order" "$PLAN_FILE")

    # Skip until we reach --from story
    if [[ "$STARTED" == false ]]; then
        if [[ "$STORY_ID" == "$START_FROM" ]]; then
            STARTED=true
        else
            continue
        fi
    fi

    # Check if already done in progress.txt
    if grep -q "$STORY_ID.*DONE" "$PROGRESS_FILE" 2>/dev/null; then
        echo "[$STORY_ORDER/$TOTAL] $STORY_ID — SKIP (already done)"
        continue
    fi

    echo "---"
    echo "[$STORY_ORDER/$TOTAL] $STORY_ID — $STORY_TITLE"
    echo "Phase: $STORY_PHASE"
    echo ""

    if [[ "$DRY_RUN" == true ]]; then
        echo "[DRY RUN] Would run codex with:"
        echo "  Story: $STORY_ID — $STORY_TITLE"
        echo "  Phase: $STORY_PHASE"
        echo ""
        continue
    fi

    # Record start
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$TIMESTAMP] $STORY_ID — START — $STORY_TITLE" >> "$PROGRESS_FILE"

    STORY_DONE=false
    ATTEMPT=0
    LAST_ERROR=""

    while [[ "$STORY_DONE" == false ]] && [[ $ATTEMPT -le $MAX_RETRIES ]]; do
        ATTEMPT=$((ATTEMPT + 1))

        if [[ $ATTEMPT -gt 1 ]]; then
            echo ""
            echo "  ↻ Retry $((ATTEMPT - 1))/$MAX_RETRIES for $STORY_ID..."
            TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            echo "[$TIMESTAMP] $STORY_ID — RETRY — Attempt $ATTEMPT: $LAST_ERROR" >> "$PROGRESS_FILE"
            sleep 5
        fi

        # Run Codex
        if [[ $ATTEMPT -eq 1 ]]; then
            echo "Running codex for $STORY_ID..."
        fi

        CODEX_OUTPUT=""
        if [[ $ATTEMPT -eq 1 ]]; then
            # First attempt — normal prompt
            if run_codex "$STORY_ID" "$STORY_TITLE"; then
                CODEX_OUTPUT="ok"
            fi
        else
            # Retry attempt — include error context in prompt
            if run_codex_retry "$STORY_ID" "$STORY_TITLE" "$LAST_ERROR"; then
                CODEX_OUTPUT="ok"
            fi
        fi

        if [[ -z "$CODEX_OUTPUT" ]]; then
            # Codex crashed
            LAST_ERROR="Codex execution failed"
            echo "  ✗ Codex failed (attempt $ATTEMPT)"

            if [[ $ATTEMPT -gt $MAX_RETRIES ]]; then
                TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
                echo "[$TIMESTAMP] $STORY_ID — BLOCKED — Codex failed after $ATTEMPT attempts" >> "$PROGRESS_FILE"
                FAILED=$((FAILED + 1))
                echo ""
                echo "[$STORY_ORDER/$TOTAL] $STORY_ID — BLOCKED (after $ATTEMPT attempts)"
                echo ""
                echo "Stopping: codex failed on $STORY_ID after $MAX_RETRIES retries"
                echo "Fix the issues and run: ./ralph.sh --from $STORY_ID"
                break 2
            fi
            continue
        fi

        # -------------------------------------------------------
        # Post-story: Run migrations as safety net
        # -------------------------------------------------------
        run_migrations

        # -------------------------------------------------------
        # Post-story: Run validation
        # -------------------------------------------------------
        VALIDATION_OK=true
        VALIDATION_ERRORS=""
        echo "Running validation..."

        if [[ "$REQUIRES_REAL_TESTS" == "true" ]] && validation_policy_contains "block_on" "test"; then
            if [[ -z "$TEST_CMD" ]] || [[ "$TEST_RUNNER" == "none" ]]; then
                echo "Tests: FAIL"
                VALIDATION_OK=false
                append_validation_error "Tests" "No real test runner is configured in .openclaw/commands.json"
            else
                run_validation_command "test" "$TEST_CMD" "Tests"
            fi
        else
            run_validation_command "test" "$TEST_CMD" "Tests"
        fi

        run_validation_command "lint" "$LINT_CMD" "Lint"
        run_validation_command "typecheck" "$TYPECHECK_CMD" "Typecheck"
        run_validation_command "build" "$BUILD_CMD" "Build"

        # Orphan route detection: warn about pages outside [locale]/
        # that would be intercepted by i18n middleware redirects.
        if [[ -f "$SCRIPT_DIR/middleware.ts" ]] && grep -q "locale" "$SCRIPT_DIR/middleware.ts" 2>/dev/null; then
            ORPHANS=""
            while IFS= read -r route_file; do
                # Derive URL path: strip src/app prefix, remove route groups (parenthesized dirs)
                url_path=$(echo "$route_file" | sed 's|^src/app/||' | sed 's|/page[.]tsx$||' | sed 's|([^/]*)/||g')
                if [[ -n "$url_path" ]]; then
                    ORPHANS="$ORPHANS  - $route_file -> /$url_path (unreachable — middleware redirects to /[locale]/$url_path)\\n"
                fi
            done < <(find "$SCRIPT_DIR/src/app" -name "page.tsx" -not -path "*/\\[locale\\]/*" -not -path "*/api/*" -not -path "*/_*" 2>/dev/null | sed "s|^$SCRIPT_DIR/||" | grep -v "^src/app/page.tsx$")
            if [[ -n "$ORPHANS" ]]; then
                echo "Orphan routes: WARN"
                echo -e "  Possible orphan routes (middleware redirects these):\\n$ORPHANS"
            fi
        fi

        if [[ "$VALIDATION_OK" == true ]]; then
            TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            if [[ $ATTEMPT -gt 1 ]]; then
                echo "[$TIMESTAMP] $STORY_ID — DONE — $STORY_TITLE (succeeded on attempt $ATTEMPT)" >> "$PROGRESS_FILE"
            else
                echo "[$TIMESTAMP] $STORY_ID — DONE — $STORY_TITLE" >> "$PROGRESS_FILE"
            fi
            echo ""
            echo "[$STORY_ORDER/$TOTAL] $STORY_ID — DONE"
            IMPLEMENTED=$((IMPLEMENTED + 1))
            STORY_DONE=true
        else
            LAST_ERROR="$VALIDATION_ERRORS"
            echo "  ✗ Validation failed (attempt $ATTEMPT)"

            if [[ $ATTEMPT -gt $MAX_RETRIES ]]; then
                TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
                echo "[$TIMESTAMP] $STORY_ID — VALIDATION — Failed after $ATTEMPT attempts: $VALIDATION_ERRORS" >> "$PROGRESS_FILE"
                FAILED=$((FAILED + 1))
                echo ""
                echo "[$STORY_ORDER/$TOTAL] $STORY_ID — VALIDATION FAILED (after $ATTEMPT attempts)"
                echo ""
                echo "Stopping: validation failed on $STORY_ID after $MAX_RETRIES retries"
                echo "Fix the issues and run: ./ralph.sh --from $STORY_ID"
                break 2
            fi
        fi
    done
done

echo ""
echo "=== Ralph Loop Complete ==="
echo "Implemented: $IMPLEMENTED"
echo "Failed: $FAILED"
echo "Total: $TOTAL"
echo ""

if [[ $FAILED -gt 0 ]]; then
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
