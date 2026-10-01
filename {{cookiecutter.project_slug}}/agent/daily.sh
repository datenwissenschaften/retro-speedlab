#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${PROJECT_DIR}/dokku/settings.sh"
readonly DOKKU_HOST="$(setting dokku.host)"
readonly HOST_ADDRESS="$(setting dokku.host_address)"
readonly RUN_HOURS="$(setting agent.hours)h"
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
timeout "${RUN_HOURS}" claude -p "$(cat agent/PROMPT.md)" \
    --permission-mode acceptEdits --output-format stream-json --verbose >"${log}" 2>&1
