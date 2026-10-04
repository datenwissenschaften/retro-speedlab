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
readonly DOKKU_HOST="$(setting dokku.host)"
readonly HOST_ADDRESS="$(setting dokku.host_address)"
readonly DEADLINE="$(( $(date +%s) + $(setting agent.hours) * 3600 ))"
readonly WRAP_UP_SECONDS=1200
readonly MODEL="$(setting agent.model)"
readonly AGENT_KEY="/workspace/.ssh/agent_key"

git config --global --add safe.directory '*'
git config --global user.name "$(setting agent.git_name)"
git config --global user.email "$(setting agent.git_email)"
mkdir -p "${HOME}/.ssh"
printf 'Host %s\n  HostName %s\n  User dokku\n  IdentityFile %s\n  IdentitiesOnly yes\n  StrictHostKeyChecking accept-new\n' \
    "${DOKKU_HOST}" "${HOST_ADDRESS}" "${AGENT_KEY}" >"${HOME}/.ssh/config"

cd "${PROJECT_DIR}"
mkdir -p agent/logs
log="agent/logs/$(date -u +%Y-%m-%dT%H%M).jsonl"
claude_options=(
    --model "${MODEL}"
    --permission-mode acceptEdits
    --allowedTools Bash Read Edit Write Glob Grep WebSearch WebFetch Monitor
    --disallowedTools "Bash(sudo:*)" "Bash(git push:*)" "Bash(rm -rf /app:*)" "Edit(/app/working/**)" "Write(/app/working/**)"
    --add-dir /app/working
    --output-format stream-json --verbose
)

seconds_left() {
    echo $(( DEADLINE - $(date +%s) ))
}

timeout "$(seconds_left)" claude -p "$(cat agent/PROMPT.md)" "${claude_options[@]}" >>"${log}" 2>&1 || true
while (( $(seconds_left) > WRAP_UP_SECONDS )); do
    timeout "$(seconds_left)" claude -p --continue "$(( $(seconds_left) / 60 )) minutes of this run are left. \
Keep working toward the level end as agent/PROMPT.md says, from where you stopped. \
Update the same report and commit before you stop." "${claude_options[@]}" >>"${log}" 2>&1 || break
done
