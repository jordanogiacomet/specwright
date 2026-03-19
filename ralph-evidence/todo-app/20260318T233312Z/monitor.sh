#!/usr/bin/env bash
set -euo pipefail

EVID_BASE="${1:?evidence dir required}"
PROJECT="${2:?project dir required}"
RALPH_PID="${3:?ralph pid required}"
CODEX_FILE="${4:?codex file required}"
PROMPT_FILE="${5:?prompt file required}"

progress_tail_pid=""
codex_tail_pid=""

cleanup() {
    if [[ -n "$progress_tail_pid" ]]; then
        kill "$progress_tail_pid" 2>/dev/null || true
    fi
    if [[ -n "$codex_tail_pid" ]]; then
        kill "$codex_tail_pid" 2>/dev/null || true
    fi
}

log_process_state() {
    {
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Ralph state"
        ps -fp "$RALPH_PID" || true
        echo
        echo "children of ralph:"
        pgrep -P "$RALPH_PID" -a || true
        for child in $(pgrep -P "$RALPH_PID" || true); do
            echo
            echo "children of $child:"
            pgrep -P "$child" -a || true
        done
        echo
    } >> "$EVID_BASE/process.monitor.log"
}

log_file_state() {
    {
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] file state"
        stat -c "%y %s %n" "$PROJECT/progress.txt" "$CODEX_FILE" "$PROMPT_FILE" 2>/dev/null || true
        echo
    } >> "$EVID_BASE/file-state.log"
}

trap cleanup EXIT

touch "$EVID_BASE/progress.follow.log" "$EVID_BASE/codex-last-message.follow.log" "$EVID_BASE/process.monitor.log"

tail -n +1 -F "$PROJECT/progress.txt" >> "$EVID_BASE/progress.follow.log" 2>&1 &
progress_tail_pid=$!

if [[ -e "$CODEX_FILE" ]]; then
    tail -n +1 -F "$CODEX_FILE" >> "$EVID_BASE/codex-last-message.follow.log" 2>&1 &
    codex_tail_pid=$!
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] monitor started" >> "$EVID_BASE/process.monitor.log"

while kill -0 "$RALPH_PID" 2>/dev/null; do
    log_process_state
    log_file_state
    sleep 10
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Ralph process exited" >> "$EVID_BASE/process.monitor.log"
log_process_state
log_file_state
