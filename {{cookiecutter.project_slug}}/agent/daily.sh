#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
readonly ENV_FILE="${HOME}/.config/speedlab/claude.env"
readonly RUN_HOURS="4h"

cd "${PROJECT_DIR}"
set -a
source "${ENV_FILE}"
set +a
export PATH="${HOME}/.local/bin:${PATH}"
mkdir -p agent/logs
log="agent/logs/$(date -u +%Y-%m-%dT%H%M).jsonl"
timeout "${RUN_HOURS}" claude -p "$(cat agent/PROMPT.md)" \
    --permission-mode acceptEdits --output-format stream-json --verbose > "${log}" 2>&1
