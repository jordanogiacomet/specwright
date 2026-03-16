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
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
STORIES_DIR="$SCRIPT_DIR/docs/stories"
MIGRATION_CMD="npx payload migrate"

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

# -------------------------------------------------------
# Auth check
# -------------------------------------------------------

if [[ "$DRY_RUN" == false ]]; then
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        echo "Error: OPENAI_API_KEY is not set."
        echo ""
        echo "Set it with:"
        echo "  export OPENAI_API_KEY=sk-..."
        echo ""
        echo "Then run this script again."
        exit 1
    fi
    echo "Auth: OK (OPENAI_API_KEY is set)"
    echo ""
fi

# -------------------------------------------------------
# Migration runner
# -------------------------------------------------------

run_migrations() {
    # Only run if node_modules exists (project has been installed)
    if [[ ! -d "$SCRIPT_DIR/node_modules" ]]; then
        return 0
    fi

    # Only run if there's a database configured
    if [[ ! -f "$SCRIPT_DIR/docker-compose.yml" ]] && [[ -z "${DATABASE_URI:-}" ]]; then
        return 0
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
    if eval "cd \"$SCRIPT_DIR\" && $MIGRATION_CMD" 2>&1; then
        echo "  Migrations: OK"
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

    # Build prompt file
    cat > "$prompt_file" <<PROMPT_EOF
# Task: Implement $story_id — $story_title

You are implementing a single story for the project **Editorial E2E Test**.

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
2. Generate a migration: `$MIGRATION_CMD:create`
3. Run the migration: `$MIGRATION_CMD`
4. Verify with: `$MIGRATION_CMD:status`

Skipping this will cause runtime errors like "relation does not exist".

## Validation

After implementation, run available validation commands (test, lint, build).
If no commands exist yet, note that in your response.
PROMPT_EOF

    # Run Codex via npx
    npx -y @openai/codex@latest exec \\
        --model gpt-5.4 \\
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

    # Build retry prompt with error context
    cat > "$prompt_file" <<PROMPT_EOF
# RETRY: Fix $story_id — $story_title

You are RETRYING a story that failed on the previous attempt for the project **Editorial E2E Test**.

## Previous Error

The previous attempt failed with:

\`\`\`
$previous_error
\`\`\`

## What to do

1. Read the error above carefully
2. Identify what went wrong (build error, missing migration, type error, test failure)
3. Fix ONLY the issue described — do not rewrite the entire story
4. Run validation to confirm the fix works

## Story

$(if [[ -f "$STORIES_DIR/$story_id.md" ]]; then cat "$STORIES_DIR/$story_id.md"; else echo "Implement: $story_title"; fi)

## CRITICAL: Database Migrations

If the error is about missing tables or columns ("relation does not exist"):
1. Generate a migration: `$MIGRATION_CMD:create`
2. Run the migration: `$MIGRATION_CMD`

## Validation

After fixing, run: test, lint, build.
PROMPT_EOF

    # Run Codex via npx
    npx -y @openai/codex@latest exec \\
        --model gpt-5.4 \\
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

        if [[ -f "$SCRIPT_DIR/package.json" ]]; then
            echo "Running validation..."

            TEST_OUTPUT=""
            if ! TEST_OUTPUT=$(npm test --if-present 2>&1); then
                echo "Tests: FAIL"
                VALIDATION_OK=false
                VALIDATION_ERRORS="Test failure: $(echo "$TEST_OUTPUT" | tail -20)"
            else
                echo "Tests: PASS"
            fi

            LINT_OUTPUT=""
            if ! LINT_OUTPUT=$(npm run lint --if-present 2>&1); then
                echo "Lint: FAIL"
                # Lint failures are warnings, don't block
            else
                echo "Lint: PASS"
            fi

            BUILD_OUTPUT=""
            if ! BUILD_OUTPUT=$(npm run build 2>&1); then
                echo "Build: FAIL"
                VALIDATION_OK=false
                if [[ -n "$VALIDATION_ERRORS" ]]; then
                    VALIDATION_ERRORS="$VALIDATION_ERRORS | Build failure: $(echo "$BUILD_OUTPUT" | tail -20)"
                else
                    VALIDATION_ERRORS="Build failure: $(echo "$BUILD_OUTPUT" | tail -20)"
                fi
            else
                echo "Build: PASS"
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
