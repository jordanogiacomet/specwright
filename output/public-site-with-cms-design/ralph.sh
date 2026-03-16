#!/usr/bin/env bash
set -euo pipefail

# ralph.sh — Story-by-story execution loop for public site with cms design
# Usage: ./ralph.sh [--dry-run] [--from ST-XXX]
#
# This script reads .openclaw/execution-plan.json, finds the next
# pending story, builds a prompt file, and runs Codex CLI to implement it.
# After each story, it runs validation and records progress.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAN_FILE="$SCRIPT_DIR/.openclaw/execution-plan.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
STORIES_DIR="$SCRIPT_DIR/docs/stories"

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

You are implementing a single story for the project **public site with cms design**.

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

## Validation

After implementation, run available validation commands (test, lint, build).
If no commands exist yet, note that in your response.
PROMPT_EOF

    # Run Codex via npx
    npx -y @openai/codex@latest exec \
        --model gpt-5.4 \
        --config 'model_reasoning_effort="xhigh"' \
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
# Read execution plan
# -------------------------------------------------------

TOTAL=$(jq '.total_stories' "$PLAN_FILE")
echo ""
echo "=== Ralph Loop: public site with cms design ==="
echo "Stories: $TOTAL"
echo "Project: $SCRIPT_DIR"
echo ""

STARTED=false
if [[ -z "$START_FROM" ]]; then
    STARTED=true
fi

IMPLEMENTED=0
FAILED=0

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

    # Run Codex
    echo "Running codex for $STORY_ID..."
    if run_codex "$STORY_ID" "$STORY_TITLE"; then
        # Run validation if available
        VALIDATION_OK=true

        if [[ -f "$SCRIPT_DIR/package.json" ]]; then
            echo "Running validation..."

            if npm test --if-present 2>&1; then
                echo "Tests: PASS"
            else
                echo "Tests: FAIL"
                VALIDATION_OK=false
            fi

            if npm run lint --if-present 2>&1; then
                echo "Lint: PASS"
            else
                echo "Lint: FAIL"
            fi
        fi

        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        if [[ "$VALIDATION_OK" == true ]]; then
            echo "[$TIMESTAMP] $STORY_ID — DONE — $STORY_TITLE" >> "$PROGRESS_FILE"
            echo ""
            echo "[$STORY_ORDER/$TOTAL] $STORY_ID — DONE"
            IMPLEMENTED=$((IMPLEMENTED + 1))
        else
            echo "[$TIMESTAMP] $STORY_ID — VALIDATION — Tests failed after implementation" >> "$PROGRESS_FILE"
            echo ""
            echo "[$STORY_ORDER/$TOTAL] $STORY_ID — VALIDATION FAILED"
            FAILED=$((FAILED + 1))
            echo ""
            echo "Stopping: validation failed on $STORY_ID"
            echo "Fix the issues and run: ./ralph.sh --from $STORY_ID"
            break
        fi
    else
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        echo "[$TIMESTAMP] $STORY_ID — BLOCKED — Codex execution failed" >> "$PROGRESS_FILE"
        FAILED=$((FAILED + 1))
        echo ""
        echo "[$STORY_ORDER/$TOTAL] $STORY_ID — BLOCKED"
        echo ""
        echo "Stopping: codex failed on $STORY_ID"
        echo "Fix the issues and run: ./ralph.sh --from $STORY_ID"
        break
    fi
done

echo ""
echo "=== Ralph Loop Complete ==="
echo "Implemented: $IMPLEMENTED"
echo "Failed: $FAILED"
echo "Total: $TOTAL"
echo ""
