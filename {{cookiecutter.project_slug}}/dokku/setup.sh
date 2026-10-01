#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${PROJECT_DIR}/dokku/settings.sh"
readonly DOKKU_HOST="$(setting dokku.host)"
readonly SERVER_HOST="$(setting dokku.server)"
readonly APP="$(setting dokku.app)"
readonly DATA_DIR="$(setting dokku.data_dir)"
readonly WORKSPACE_DIR="$(setting dokku.workspace_dir)"
readonly AGENT_KEY="${WORKSPACE_DIR}/.ssh/agent_key"

dokku() {
    ssh "${DOKKU_HOST}" "$@"
}

ssh -t "${SERVER_HOST}" sudo mkdir -p "${DATA_DIR}/working" "${DATA_DIR}/huggingface"
ssh "${SERVER_HOST}" "mkdir -p ${WORKSPACE_DIR}/.ssh && chmod 700 ${WORKSPACE_DIR}/.ssh \
    && { test -f ${AGENT_KEY} || ssh-keygen -q -t ed25519 -N '' -C ${APP}-agent -f ${AGENT_KEY}; }"
dokku apps:exists "${APP}" || dokku apps:create "${APP}"
dokku docker-options:add "${APP}" deploy,run "--gpus=all"
dokku docker-options:add "${APP}" deploy,run "--shm-size=2g"
dokku storage:mount "${APP}" "${DATA_DIR}/working:/app/working"
dokku storage:mount "${APP}" "${DATA_DIR}/huggingface:/root/.cache/huggingface"
dokku storage:mount "${APP}" "${WORKSPACE_DIR}:/workspace"
ssh "${SERVER_HOST}" cat "${AGENT_KEY}.pub" | ssh -t "${SERVER_HOST}" sudo dokku ssh-keys:add "${APP}-agent"
dokku ports:set "${APP}" http:80:18080
dokku checks:disable "${APP}"
dokku checks:set "${APP}" wait-to-retire 0
echo "Set the agent token once: ssh ${DOKKU_HOST} config:set --no-restart ${APP} CLAUDE_CODE_OAUTH_TOKEN=<token>"
