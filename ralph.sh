#!/bin/bash
# Ralph Loop — Initializer Story Runner
# Usage: ./ralph.sh [max_iterations]

set -euo pipefail

MAX_ITERATIONS="${1:-20}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PRD_FILE="$SCRIPT_DIR/prd.json"
ARCHITECTURE_FILE="$SCRIPT_DIR/architecture.md"
DIAGNOSIS_FILE="$SCRIPT_DIR/diagnosis.md"
DECISIONS_FILE="$SCRIPT_DIR/decisions.md"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
AGENTS_FILE="$SCRIPT_DIR/AGENTS.md"

require_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Error: missing $file"
    exit 1
  fi
}

require_file "$PRD_FILE"
require_file "$ARCHITECTURE_FILE"
require_file "$DIAGNOSIS_FILE"
require_file "$DECISIONS_FILE"
require_file "$PROGRESS_FILE"
require_file "$AGENTS_FILE"

append_progress() {
  local type="$1"
  local message="$2"
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "[$timestamp] $type — $message" >> "$PROGRESS_FILE"
}

validate_prd_story_model() {
  python3 - "$PRD_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

stories = data.get("stories")
if not isinstance(stories, list) or not stories:
    print("Error: prd.json must contain a non-empty root 'stories' array.")
    sys.exit(1)

required_fields = {"id", "title", "status", "type", "description", "acceptance_criteria"}
allowed_statuses = {"todo", "in_progress", "done", "blocked"}

for idx, story in enumerate(stories):
    if not isinstance(story, dict):
        print(f"Error: story at index {idx} is not an object.")
        sys.exit(1)

    missing = required_fields - set(story.keys())
    if missing:
        print(f"Error: story {story.get('id', f'index {idx}')} is missing fields: {sorted(missing)}")
        sys.exit(1)

    if story["status"] not in allowed_statuses:
        print(f"Error: story {story['id']} has invalid status '{story['status']}'.")
        sys.exit(1)

    if not isinstance(story["acceptance_criteria"], list):
        print(f"Error: story {story['id']} acceptance_criteria must be a list.")
        sys.exit(1)
PY
}

get_current_stop_mode() {
  python3 - "$PRD_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

mode = (
    data.get("execution_model", {})
        .get("current_stop_mode", "diagnosis_iteration")
)
print(mode)
PY
}

get_required_story_ids_for_current_mode() {
  python3 - "$PRD_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

mode = data.get("execution_model", {}).get("current_stop_mode", "diagnosis_iteration")
stop_conditions = data.get("execution_model", {}).get("stop_conditions", {})

mapping = {
    "diagnosis_iteration": "diagnosis_iteration_complete_when_story_ids_done",
    "minimum_working": "minimum_working_complete_when_story_ids_done",
}

key = mapping.get(mode)
if not key:
    sys.exit(1)

story_ids = stop_conditions.get(key, [])
if not isinstance(story_ids, list):
    sys.exit(1)

for story_id in story_ids:
    print(story_id)
PY
}

all_required_stories_done() {
  python3 - "$PRD_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

stories = data.get("stories", [])
story_map = {story["id"]: story for story in stories if isinstance(story, dict) and "id" in story}

mode = data.get("execution_model", {}).get("current_stop_mode", "diagnosis_iteration")
stop_conditions = data.get("execution_model", {}).get("stop_conditions", {})

mapping = {
    "diagnosis_iteration": "diagnosis_iteration_complete_when_story_ids_done",
    "minimum_working": "minimum_working_complete_when_story_ids_done",
}

key = mapping.get(mode)
if not key:
    sys.exit(1)

required_ids = stop_conditions.get(key, [])
if not isinstance(required_ids, list) or not required_ids:
    sys.exit(1)

for story_id in required_ids:
    story = story_map.get(story_id)
    if not story:
        sys.exit(1)
    if story.get("status") != "done":
        sys.exit(1)

sys.exit(0)
PY
}

get_next_story_json() {
  python3 - "$PRD_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

stories = data.get("stories", [])
story_map = {story["id"]: story for story in stories if isinstance(story, dict) and "id" in story}

mode = data.get("execution_model", {}).get("current_stop_mode", "diagnosis_iteration")
stop_conditions = data.get("execution_model", {}).get("stop_conditions", {})

mapping = {
    "diagnosis_iteration": "diagnosis_iteration_complete_when_story_ids_done",
    "minimum_working": "minimum_working_complete_when_story_ids_done",
}

key = mapping.get(mode)
if not key:
    sys.exit(1)

required_ids = stop_conditions.get(key, [])
if not isinstance(required_ids, list) or not required_ids:
    sys.exit(1)

selected = None

for story_id in required_ids:
    story = story_map.get(story_id)
    if story and story.get("status") == "in_progress":
        selected = story
        break

if selected is None:
    for story_id in required_ids:
        story = story_map.get(story_id)
        if story and story.get("status") == "todo":
            selected = story
            break

if selected is None:
    sys.exit(1)

print(json.dumps(selected, ensure_ascii=False, indent=2))
PY
}

get_next_story_id() {
  python3 - "$PRD_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

stories = data.get("stories", [])
story_map = {story["id"]: story for story in stories if isinstance(story, dict) and "id" in story}

mode = data.get("execution_model", {}).get("current_stop_mode", "diagnosis_iteration")
stop_conditions = data.get("execution_model", {}).get("stop_conditions", {})

mapping = {
    "diagnosis_iteration": "diagnosis_iteration_complete_when_story_ids_done",
    "minimum_working": "minimum_working_complete_when_story_ids_done",
}

key = mapping.get(mode)
if not key:
    sys.exit(1)

required_ids = stop_conditions.get(key, [])
if not isinstance(required_ids, list) or not required_ids:
    sys.exit(1)

selected = None

for story_id in required_ids:
    story = story_map.get(story_id)
    if story and story.get("status") == "in_progress":
        selected = story
        break

if selected is None:
    for story_id in required_ids:
        story = story_map.get(story_id)
        if story and story.get("status") == "todo":
            selected = story
            break

if selected is None:
    sys.exit(1)

print(selected["id"])
PY
}

build_prompt() {
  local iteration="$1"
  local stop_mode="$2"
  local story_id="$3"
  local story_json="$4"
  local prompt_file="$5"

  cat > "$prompt_file" <<EOF
You are running inside the OpenClaw Project Initializer repository through Ralph loop.

Follow AGENTS.md exactly.

Execution wrapper for this run:
- The canonical backlog is stored in prd.json under root "stories".
- Work on exactly one story only.
- The selected story for this iteration is: ${story_id}
- The active stop mode is: ${stop_mode}
- Before changing anything, read the repository documents and learn what the project currently does from the code.
- Preserve the main idea of the project.
- Do not redesign the product.
- Do not invent unrelated scope.
- Update progress.txt with what you learned, what you changed, and what validation you actually ran.
- Update only the selected story status in prd.json when justified:
  - use "in_progress" when the story has started but is not complete
  - use "done" only when the acceptance criteria are genuinely satisfied
  - use "blocked" only when a real blocker prevents completion
- Do not advance unrelated stories in the same run.
- Do not touch production, deploy, or perform unrelated refactors.
- If blocked, record the blocker in progress.txt and stop.

Required read order for this run:
1. progress.txt
2. decisions.md
3. diagnosis.md
4. architecture.md
5. prd.json
6. AGENTS.md
7. the selected story object below
8. the relevant implementation files needed for this story

Required reasoning order for this run:
1. Learn what the current implementation does for this story
2. Compare it with the intended repository model
3. Complete the smallest coherent step needed for the selected story
4. Validate what you actually changed
5. Update the selected story status in prd.json appropriately

Completion rule for this exec call:
- Print exactly COMPLETE only if the active stop mode's required stories are all done.
- Otherwise print a short result summary for the selected story only.

Selected story JSON:
${story_json}

Below is AGENTS.md for repository-local operating rules.
EOF

  cat "$AGENTS_FILE" >> "$prompt_file"
}

run_codex() {
  local iteration="$1"
  local stop_mode="$2"
  local story_id="$3"
  local story_json="$4"
  local prompt_file
  local output_file

  prompt_file="$(mktemp "$SCRIPT_DIR/.ralph-prompt.XXXXXX.md")"
  output_file="$(mktemp "$SCRIPT_DIR/.codex-last-message.XXXXXX.txt")"

  cleanup() {
    rm -f "$prompt_file" "$output_file"
  }
  trap cleanup RETURN

  build_prompt "$iteration" "$stop_mode" "$story_id" "$story_json" "$prompt_file"

  npx -y @openai/codex@latest exec \
    --model gpt-5.4 \
    --config 'model_reasoning_effort="xhigh"' \
    --sandbox danger-full-access \
    --json \
    --output-last-message "$output_file" \
    - < "$prompt_file"

  if [[ -f "$output_file" ]]; then
    cat "$output_file"
  fi
}

validate_prd_story_model

STOP_MODE="$(get_current_stop_mode)"

echo "Starting Ralph Loop — Initializer Story Runner"
echo "Max iterations: $MAX_ITERATIONS"
echo "Stop mode: $STOP_MODE"
echo "PRD: $PRD_FILE"
echo "Architecture: $ARCHITECTURE_FILE"
echo "Diagnosis: $DIAGNOSIS_FILE"
echo "Decisions: $DECISIONS_FILE"
echo "Progress: $PROGRESS_FILE"
echo "Prompt source: $AGENTS_FILE"

append_progress "INFO" "Ralph loop started. Max iterations: $MAX_ITERATIONS. Stop mode: $STOP_MODE."

if all_required_stories_done; then
  echo "Active stop mode already satisfied."
  append_progress "INFO" "Ralph loop exited immediately because all required stories for stop mode '$STOP_MODE' were already done."
  exit 0
fi

for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo ""
  echo "==============================================================="
  echo " Ralph Loop Iteration $i of $MAX_ITERATIONS"
  echo "==============================================================="

  if all_required_stories_done; then
    echo "Active stop mode completed."
    append_progress "INFO" "Ralph loop finished because all required stories for stop mode '$STOP_MODE' are done."
    exit 0
  fi

  NEXT_STORY_JSON="$(get_next_story_json || true)"
  NEXT_STORY_ID="$(get_next_story_id || true)"

  if [[ -z "${NEXT_STORY_JSON:-}" || -z "${NEXT_STORY_ID:-}" ]]; then
    echo "No selectable story found for current stop mode."
    append_progress "BLOCKED" "No selectable story found for stop mode '$STOP_MODE'. Check prd.json story statuses."
    exit 1
  fi

  echo "Selected story: $NEXT_STORY_ID"
  append_progress "INFO" "Starting iteration $i for story $NEXT_STORY_ID under stop mode '$STOP_MODE'."

  OUTPUT="$(run_codex "$i" "$STOP_MODE" "$NEXT_STORY_ID" "$NEXT_STORY_JSON" 2>&1 | tee /dev/stderr)" || true

  if all_required_stories_done; then
    echo ""
    echo "Active stop mode completed."
    append_progress "INFO" "All required stories for stop mode '$STOP_MODE' completed after iteration $i."
    exit 0
  fi

  if echo "$OUTPUT" | grep -q "^COMPLETE$"; then
    echo ""
    echo "Ralph loop reported COMPLETE."
    append_progress "INFO" "Ralph loop received COMPLETE from Codex on iteration $i."
    exit 0
  fi

  append_progress "INFO" "Iteration $i completed for story $NEXT_STORY_ID."
  echo "Iteration $i complete."
  sleep 2
done

echo ""
echo "Ralph loop reached max iterations ($MAX_ITERATIONS)."
echo "Check $PROGRESS_FILE and $PRD_FILE for current status."
append_progress "INFO" "Ralph loop reached max iterations without satisfying stop mode '$STOP_MODE'."
exit 1