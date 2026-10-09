#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
readonly WORKSPACE_DIR="$(dirname "${PROJECT_DIR}")"
readonly RUNS_LOG="${WORKSPACE_DIR}/.agent-runs"
readonly LAST_RUN_END="${WORKSPACE_DIR}/.agent-last-run"
readonly PROGRESS_FILES="/app/working/cache/curriculum/*/*.successes"
source "${PROJECT_DIR}/dokku/settings.sh"
readonly STALL_SECONDS="$(( $(setting agent.stall_hours) * 3600 ))"
readonly RUNS_PER_DAY="$(setting agent.runs_per_day)"

last_progress() {
    # shellcheck disable=SC2086
    { stat -c %Y ${PROGRESS_FILES} "${LAST_RUN_END}" 2>/dev/null || true; } | sort -n | tail -1
}

if [[ -e "${WORKSPACE_DIR}/.lab-run" ]]; then
    echo "No lab run: one is running"
    exit 0
fi
today="$(date -u +%F)"
runs_today="$(grep -c "^${today}" "${RUNS_LOG}" 2>/dev/null || true)"
if (( ${runs_today:-0} >= RUNS_PER_DAY )); then
    echo "No lab run: ${runs_today} of ${RUNS_PER_DAY} runs today"
    exit 0
fi
since="$(last_progress)"
stalled="$(( $(date +%s) - ${since:-0} ))"
if (( stalled < STALL_SECONDS )); then
    echo "No lab run: the last progress was $(( stalled / 60 )) minutes ago"
    exit 0
fi
echo "Lab run: no progress for $(( stalled / 60 )) minutes, run $(( ${runs_today:-0} + 1 )) of ${RUNS_PER_DAY} today"
date -u +%FT%TZ >>"${RUNS_LOG}"
exec "${PROJECT_DIR}/agent/daily.sh"
