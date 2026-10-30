#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
readonly WORKSPACE_DIR="$(dirname "${PROJECT_DIR}")"

restore_workspace_owner() {
    chown -R "$(stat -c %u:%g "${WORKSPACE_DIR}")" "${WORKSPACE_DIR}"
}
trap restore_workspace_owner EXIT

exec {lock}>"${WORKSPACE_DIR}/.agent.lock"
flock --nonblock "${lock}" || { echo "A lab run is active" >&2; exit 0; }
source "${PROJECT_DIR}/dokku/settings.sh"
readonly RUNS=5
readonly CRITIC_SECONDS=180
readonly CRITIC="${WORKSPACE_DIR}/.lab-critic.json"
readonly LESSONS="agent/LESSONS.md"
readonly ANSWER="$(mktemp)"
readonly SCHEMA='{"type": "object", "additionalProperties": false, "required": ["lessons"], "properties": {"lessons":
    {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 100, "pattern": "^[ -~]+$"}}}}'

git config --global --add safe.directory '*'
cd "${PROJECT_DIR}"
reports=(agent/reports/*.md)
reports=("${reports[@]: -${RUNS}}")
timeout "${CRITIC_SECONDS}" claude -p "$(cat agent/CRITIC.md)

Reports to review: ${reports[*]}" \
    --model "$(setting agent.model)" --tools Read Glob Grep --allowedTools Read Glob Grep \
    --output-format json --json-schema "${SCHEMA}" >"${ANSWER}"
python agent/lessons.py "${ANSWER}" "${CRITIC}" "${LESSONS}" "${RUNS}"
git add "${LESSONS}"
git diff --cached --quiet -- "${LESSONS}" || git -c user.name="$(setting agent.git_name)" \
    -c user.email="$(setting agent.git_email)" commit --quiet -m "docs(lab): lessons from the last ${RUNS} lab reports" \
    -- "${LESSONS}"
