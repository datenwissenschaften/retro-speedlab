#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
readonly WORKSPACE_DIR="$(dirname "${PROJECT_DIR}")"

restore_workspace_owner() {
    chown -R "$(stat -c %u:%g "${WORKSPACE_DIR}")" "${WORKSPACE_DIR}"
}
trap restore_workspace_owner EXIT

exec {lock}>"${WORKSPACE_DIR}/.agent.lock"
flock --nonblock "${lock}" || { echo "Another lab run is active" >&2; exit 0; }
source "${PROJECT_DIR}/dokku/settings.sh"
source "${PROJECT_DIR}/agent/work_in_progress.sh"
readonly DOKKU_HOST="$(setting dokku.host)"
readonly HOST_ADDRESS="$(setting dokku.host_address)"
readonly AGENT=claude
readonly CHECK_SECONDS=600
readonly EXTENSION_MINUTES="$(setting agent.extension_minutes)"
deadline="$(( $(date +%s) + $(setting agent.minutes) * 60 ))"
readonly LAB_RUN_MARKER="${WORKSPACE_DIR}/.lab-run"
readonly RESULT="${WORKSPACE_DIR}/.lab-duel.json"
finish() {
    rm -f "${LAB_RUN_MARKER}" "${RESULT}"
    touch "${WORKSPACE_DIR}/.agent-last-run"
    restore_workspace_owner
}
trap finish EXIT
readonly WRAP_UP_SECONDS=120
readonly IDLE_ROUND_SECONDS=120
readonly OOM_KILL_FIRST=1000
readonly MODEL="$(setting agent.model)"
readonly AGENT_KEY="/workspace/.ssh/agent_key"
readonly STAMP="$(date -u +%Y-%m-%dT%H%M)"
readonly BRANCH="lab/${STAMP}/${AGENT}"
readonly BRANCH_DIR="${PROJECT_DIR}-${AGENT}"
readonly AGENT_LOG="${PROJECT_DIR}/agent/logs/${STAMP}-${AGENT}.jsonl"

git config --global --add safe.directory '*'
git config --global user.name "$(setting agent.git_name)"
git config --global user.email "$(setting agent.git_email)"
mkdir -p "${PROJECT_DIR}/agent/logs"
readonly BASE="$(git -C "${PROJECT_DIR}" rev-parse HEAD)"
rm -f "${RESULT}"

readonly AGENT_OPTIONS=(
    --model "${MODEL}"
    --permission-mode acceptEdits
    --allowedTools Bash Read Edit Write Glob Grep WebSearch WebFetch Monitor Agent
    --disallowedTools "Bash(sudo:*)" "Bash(git push:*)" "Bash(rm -rf /app:*)" "Edit(/app/working/**)" "Write(/app/working/**)"
    --add-dir /app/working
    --output-format stream-json --verbose
)

seconds_left() {
    echo $(( deadline - $(date +%s) ))
}

continue_prompt() {
    echo "$(( $(seconds_left) / 60 )) minutes of this run are left. \
Keep working as agent/PROMPT.md says, from where you stopped. Update the same report and commit before you stop. \
If nothing useful is left to do, stop at once without a commit."
}

mark_phase() {
    local result=null
    if [[ -f "${RESULT}" ]]; then
        result="$(cat "${RESULT}")"
    fi
    printf '{"until": %s, "phase": "%s", "base": "%s", "agents": {"%s": {"log": "%s", "worktree": "%s"}}, "duel": %s}\n' \
        "$(( deadline + CHECK_SECONDS ))" "$1" "${BASE}" "${AGENT}" "${AGENT_LOG}" "${BRANCH_DIR}" "${result}" \
        >"${LAB_RUN_MARKER}.tmp"
    mv "${LAB_RUN_MARKER}.tmp" "${LAB_RUN_MARKER}"
}

open_branch() {
    git -C "${PROJECT_DIR}" worktree remove --force "${BRANCH_DIR}" 2>/dev/null || true
    git -C "${PROJECT_DIR}" worktree add --quiet -b "${BRANCH}" "${BRANCH_DIR}" HEAD
    cp "${PROJECT_DIR}/config.yaml" "${BRANCH_DIR}/config.yaml"
    cp -r "${PROJECT_DIR}/roms/." "${BRANCH_DIR}/roms/"
}

run_agent() {
    echo "${OOM_KILL_FIRST}" >/proc/self/oom_score_adj
    cd "${BRANCH_DIR}"
    timeout "$(seconds_left)" claude -p "$(cat agent/PROMPT.md)

The base commit of this run is ${BASE}." "${AGENT_OPTIONS[@]}" || true
    while (( $(seconds_left) > WRAP_UP_SECONDS )); do
        local round_start="$(date +%s)"
        timeout "$(seconds_left)" claude -p --continue "$(continue_prompt)" "${AGENT_OPTIONS[@]}" || break
        (( $(date +%s) - round_start >= IDLE_ROUND_SECONDS )) || break
    done
}

extend_agent() {
    echo "${OOM_KILL_FIRST}" >/proc/self/oom_score_adj
    cd "${BRANCH_DIR}"
    timeout "$(seconds_left)" claude -p --continue         "${EXTENSION_MINUTES} minutes extra to finish and verify; no new work." "${AGENT_OPTIONS[@]}" || true
}

accepted() {
    [[ "$(git -C "${PROJECT_DIR}" rev-list --count "${BASE}..${BRANCH}")" -gt 0 ]] || return 1
    cd "${BRANCH_DIR}"
    bash "${PROJECT_DIR}/agent/verify.sh"
}

ship() {
    git -C "${PROJECT_DIR}" merge --no-edit --quiet "${BRANCH}"
    if git -C "${PROJECT_DIR}" diff --quiet "${BASE}" HEAD -- . ':(exclude)agent'; then
        echo "Lab run ${STAMP}: only agent/ changed, the search keeps running"
        return
    fi
    mkdir -p "${HOME}/.ssh"
    printf 'Host %s\n  HostName %s\n  User dokku\n  IdentityFile %s\n  IdentitiesOnly yes\n  StrictHostKeyChecking accept-new\n' \
        "${DOKKU_HOST}" "${HOST_ADDRESS}" "${AGENT_KEY}" >"${HOME}/.ssh/config"
    bash "${PROJECT_DIR}/dokku/deploy.sh"
}

mark_phase working
open_branch
(run_agent >>"${AGENT_LOG}" 2>&1)
if work_in_progress "${BRANCH_DIR}" "${BASE}"; then
    deadline=$(( deadline + EXTENSION_MINUTES * 60 ))
    mark_phase working
    (extend_agent >>"${AGENT_LOG}" 2>&1)
fi

mark_phase judging
verdict=none
if (accepted >>"${AGENT_LOG}" 2>&1); then
    verdict="${AGENT}"
fi
printf '{"winner": "%s", "confidence": 1.0, "scores": []}\n' "${verdict}" >"${RESULT}"
echo "Lab run ${STAMP}: ${verdict}"
mark_phase decided
if [[ "${verdict}" == "${AGENT}" ]]; then
    ship
fi
git -C "${PROJECT_DIR}" worktree remove --force "${BRANCH_DIR}"
