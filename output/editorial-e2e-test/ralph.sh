#!/usr/bin/env bash
set -euo pipefail

# ralph.sh — Story-by-story execution loop for Editorial E2E Test
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
MIGRATION_CMD="npm run db:migrate"
MIGRATION_CREATE="npm run db:migrate:create"
MIGRATION_STATUS="npm run db:migrate:status"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_EFFORT="${CODEX_EFFORT:-medium}"

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

validation_policy_contains() {
    local field="$1"
    local command_name="$2"
    jq -e --arg field "$field" --arg command_name "$command_name"         '.validation[$field] // [] | index($command_name)'         "$COMMANDS_FILE" >/dev/null 2>&1
}

append_validation_error() {
    local label="$1"
    local output="$2"
    local message

    message="$label failure: $(echo "$output" | tail -20)"
    if [[ -n "$VALIDATION_ERRORS" ]]; then
        VALIDATION_ERRORS="$VALIDATION_ERRORS | $message"
    else
        VALIDATION_ERRORS="$message"
    fi
}

run_validation_command() {
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
}

# -------------------------------------------------------
# Migration runner
# -------------------------------------------------------

run_migrations() {
    local is_payload_backend=false
    local output=""

    # Only run if node_modules exists (project has been installed)
    if [[ ! -d "$SCRIPT_DIR/node_modules" ]]; then
        return 0
    fi

    # Only run if there's a database configured
    if [[ ! -f "$SCRIPT_DIR/docker-compose.yml" ]] && [[ -z "${DATABASE_URI:-}" ]]; then
        return 0
    fi

    if [[ -f "$SCRIPT_DIR/src/payload.config.ts" ]] || [[ -f "$SCRIPT_DIR/payload.config.ts" ]]; then
        is_payload_backend=true
    fi

    # Only run if the migration command is available
    # For payload: check if payload is installed
    # For npm scripts: check if the script exists in package.json
    if [[ "$MIGRATION_CMD" == "./node_modules/.bin/payload --disable-transpile migrate" ]] || [[ "$MIGRATION_CMD" == "payload --disable-transpile migrate" ]]; then
        # Check if payload is installed
        if [[ ! -x "$SCRIPT_DIR/node_modules/.bin/payload" ]]; then
            return 0
        fi
        # Check if payload config exists (means backend is set up)
        if [[ ! -f "$SCRIPT_DIR/src/payload.config.ts" ]] && [[ ! -f "$SCRIPT_DIR/payload.config.ts" ]]; then
            return 0
        fi
    elif [[ "$MIGRATION_CMD" == "npm run "* ]]; then
        # Extract script name from "npm run db:migrate"
        local script_name="${MIGRATION_CMD#npm run }"
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
    if output=$(eval "cd \"$SCRIPT_DIR\" && $MIGRATION_CMD" 2>&1); then
        if [[ "$is_payload_backend" == true ]] && printf '%s' "$output" | grep -q "__SPECWRIGHT_PAYLOAD_MIGRATIONS__:no-pending"; then
            echo "  Migrations: SKIP (no pending Payload migrations)"
        elif [[ "$is_payload_backend" == true ]] && printf '%s' "$output" | grep -q "__SPECWRIGHT_PAYLOAD_MIGRATIONS__:dev-push"; then
            echo "  Migrations: WARN (skipped Payload migrate: dev-mode push marker found in payload_migrations)"
        else
            echo "  Migrations: OK"
        fi
    else
        echo "  Migrations: WARN (command failed, may need manual intervention)"
        # Don't fail the story — the agent may not have created new migrations
    fi
}

# -------------------------------------------------------
# Codex runner
# -------------------------------------------------------

run_codex() {
    local story_id="$1"
    local story_title="$2"
    local prompt_file
    local output_file

    prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
    output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

    _cleanup() {
        rm -f "$prompt_file" "$output_file"
    }
    trap _cleanup RETURN

    # Build prompt file without evaluating story markdown in the shell
    {
        printf '# Task: Implement %s — %s\n\n' "$story_id" "$story_title"
        cat <<'PROMPT_EOF'
You are implementing a single story for the project **Editorial E2E Test**.

## Story

PROMPT_EOF
        if [[ -f "$STORIES_DIR/$story_id.md" ]]; then
            cat "$STORIES_DIR/$story_id.md"
        else
            printf 'Implement: %s\n' "$story_title"
        fi
        printf '\n\n'
        cat <<'PROMPT_EOF'
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

PROMPT_EOF
        printf '1. Make the schema change\n'
        printf '2. Generate a migration: `%s`\n' "$MIGRATION_CREATE"
        printf '3. Run the migration: `%s`\n' "$MIGRATION_CMD"
        printf '4. Verify with: `%s`\n\n' "$MIGRATION_STATUS"
        cat <<'PROMPT_EOF'
Skipping this will cause runtime errors like "relation does not exist".

## Validation

After implementation, run available validation commands (test, lint, build).
If no commands exist yet, note that in your response.
PROMPT_EOF
    } > "$prompt_file"

    # Run Codex via installed CLI
    codex exec \
        --model "$CODEX_MODEL" \
        --config "model_reasoning_effort=\"$CODEX_EFFORT\"" \
        --sandbox danger-full-access \
        --json \
        --output-last-message "$output_file" \
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
}

# -------------------------------------------------------
# Codex retry runner (includes error context)
# -------------------------------------------------------

run_codex_retry() {
    local story_id="$1"
    local story_title="$2"
    local previous_error="$3"
    local prompt_file
    local output_file

    prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
    output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

    _cleanup() {
        rm -f "$prompt_file" "$output_file"
    }
    trap _cleanup RETURN

    # Build retry prompt without evaluating error text or story markdown in the shell
    {
        printf '# RETRY: Fix %s — %s\n\n' "$story_id" "$story_title"
        cat <<'PROMPT_EOF'
You are RETRYING a story that failed on the previous attempt for the project **Editorial E2E Test**.

## Previous Error

The previous attempt failed with:

PROMPT_EOF
        printf '```\n%s\n```\n\n' "$previous_error"
        cat <<'PROMPT_EOF'
## What to do

1. Read the error above carefully
2. Identify what went wrong (build error, missing migration, type error, test failure)
3. Fix ONLY the issue described — do not rewrite the entire story
4. Run validation to confirm the fix works

## Story

PROMPT_EOF
        if [[ -f "$STORIES_DIR/$story_id.md" ]]; then
            cat "$STORIES_DIR/$story_id.md"
        else
            printf 'Implement: %s\n' "$story_title"
        fi
        printf '\n\n'
        cat <<'PROMPT_EOF'
## CRITICAL: Database Migrations

If the error is about missing tables or columns ("relation does not exist"):
PROMPT_EOF
        printf '1. Generate a migration: `%s`\n' "$MIGRATION_CREATE"
        printf '2. Run the migration: `%s`\n\n' "$MIGRATION_CMD"
        cat <<'PROMPT_EOF'
## Validation

After fixing, run: test, lint, build.
PROMPT_EOF
    } > "$prompt_file"

    # Run Codex via installed CLI
    codex exec \
        --model "$CODEX_MODEL" \
        --config "model_reasoning_effort=\"$CODEX_EFFORT\"" \
        --sandbox danger-full-access \
        --json \
        --output-last-message "$output_file" \
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
}

# -------------------------------------------------------
# Read execution plan
# -------------------------------------------------------

TOTAL=$(jq '.total_stories' "$PLAN_FILE")
echo ""
echo "=== Ralph Loop: Editorial E2E Test ==="
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
                    ORPHANS="$ORPHANS  - $route_file -> /$url_path (unreachable — middleware redirects to /[locale]/$url_path)\n"
                fi
            done < <(find "$SCRIPT_DIR/src/app" -name "page.tsx" -not -path "*/\[locale\]/*" -not -path "*/api/*" -not -path "*/_*" 2>/dev/null | sed "s|^$SCRIPT_DIR/||" | grep -v "^src/app/page.tsx$")
            if [[ -n "$ORPHANS" ]]; then
                echo "Orphan routes: WARN"
                echo -e "  Possible orphan routes (middleware redirects these):\n$ORPHANS"
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
