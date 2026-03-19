#!/usr/bin/env bash
set -euo pipefail

EVID_BASE="${1:?evidence dir required}"
PROJECT_CWD="${2:?project cwd required}"
RALPH_PID="${3:?ralph pid required}"

SESSIONS_DIR="/home/node/.codex/sessions"
OUT_DIR="$EVID_BASE/codex-sessions"
STATE_FILE="$EVID_BASE/codex-sessions.state"
LOG_FILE="$EVID_BASE/codex-sessions.monitor.log"

mkdir -p "$OUT_DIR"
touch "$STATE_FILE" "$LOG_FILE"

sync_sessions() {
    local session_file

    while IFS= read -r session_file; do
        [[ -n "$session_file" ]] || continue

        local meta
        meta="$(head -n 1 "$session_file" 2>/dev/null || true)"
        [[ -n "$meta" ]] || continue

        local originator
        local cwd
        originator="$(printf '%s\n' "$meta" | jq -r '.payload.originator // empty' 2>/dev/null || true)"
        cwd="$(printf '%s\n' "$meta" | jq -r '.payload.cwd // empty' 2>/dev/null || true)"

        if [[ "$originator" != "codex_exec" ]] || [[ "$cwd" != "$PROJECT_CWD" ]]; then
            continue
        fi

        local base
        local raw_copy
        local assistant_copy
        local commands_copy
        local user_copy

        base="$(basename "$session_file")"
        raw_copy="$OUT_DIR/$base"
        assistant_copy="$OUT_DIR/$base.assistant.txt"
        commands_copy="$OUT_DIR/$base.commands.txt"
        user_copy="$OUT_DIR/$base.user.txt"

        cp "$session_file" "$raw_copy"

        jq -r '
            select(.type=="response_item" and .payload.type=="message" and .payload.role=="assistant")
            | [.timestamp, (.payload.phase // ""), (.payload.content[]?.text // .payload.content[]?.output_text // "")]
            | @tsv
        ' "$session_file" > "$assistant_copy" 2>/dev/null || true

        jq -r '
            select(.type=="response_item" and .payload.type=="function_call_output")
            | [.timestamp, .payload.call_id, .payload.output]
            | @tsv
        ' "$session_file" > "$commands_copy" 2>/dev/null || true

        jq -r '
            select(.type=="event_msg" and .payload.type=="user_message")
            | [.timestamp, .payload.message]
            | @tsv
        ' "$session_file" > "$user_copy" 2>/dev/null || true

        printf '%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$base" >> "$STATE_FILE"
        printf '[%s] mirrored %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$base" >> "$LOG_FILE"
    done < <(find "$SESSIONS_DIR" -type f -name 'rollout-*.jsonl' | sort)

    local latest_raw
    latest_raw="$(find "$OUT_DIR" -maxdepth 1 -type f -name 'rollout-*.jsonl' | sort | tail -n 1)"
    if [[ -n "$latest_raw" ]]; then
        cp "$latest_raw" "$EVID_BASE/codex-output.current.jsonl"
        cp "$latest_raw.assistant.txt" "$EVID_BASE/codex-output.current.assistant.txt" 2>/dev/null || true
        cp "$latest_raw.commands.txt" "$EVID_BASE/codex-output.current.commands.txt" 2>/dev/null || true
        cp "$latest_raw.user.txt" "$EVID_BASE/codex-output.current.user.txt" 2>/dev/null || true
    fi
}

printf '[%s] codex session mirroring started\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG_FILE"

while kill -0 "$RALPH_PID" 2>/dev/null; do
    sync_sessions
    sleep 5
done

sync_sessions
printf '[%s] codex session mirroring finished\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG_FILE"
