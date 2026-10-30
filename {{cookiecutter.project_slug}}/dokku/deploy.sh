#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${PROJECT_DIR}/dokku/settings.sh"
readonly DOKKU_HOST="$(setting dokku.host)"
readonly APP="$(setting dokku.app)"
readonly SCHEDULE="$(setting agent.schedule)"
readonly CORE_DIR="$(cd "${PROJECT_DIR}/../retro-speedlab-core" && pwd)"
readonly CONFIG_PATH="${PROJECT_DIR}/config.yaml"
readonly GAME="$(setting training.game)"
readonly ROM_PATH="${PROJECT_DIR}/roms/${GAME}.nes"
readonly TODAY="$(date -u +%Y.%m.%d)"

if ! git -C "${CORE_DIR}" diff --quiet HEAD; then
    echo "retro-speedlab-core has uncommitted changes; commit them before deploying." >&2
    exit 1
fi

if [[ ! -f "${CONFIG_PATH}" ]]; then
    echo "Missing deployment configuration: ${CONFIG_PATH}" >&2
    exit 1
fi

if [[ ! -f "${ROM_PATH}" ]]; then
    echo "Missing deployment ROM: ${ROM_PATH}" >&2
    exit 1
fi

previous_release="$(ssh "${DOKKU_HOST}" config:get "${APP}" RELEASE 2>/dev/null)" || previous_release=""
if [[ "${previous_release}" == "${TODAY}-"* ]]; then
    release="${TODAY}-$(( ${previous_release##*-} + 1 ))"
else
    release="${TODAY}-1"
fi

build_dir="$(mktemp -d)"
trap 'rm -rf "${build_dir}"' EXIT
mkdir -p "${build_dir}/core" "${build_dir}/app"

git -C "${CORE_DIR}" archive HEAD | tar -x -C "${build_dir}/core"
tar -C "${PROJECT_DIR}" \
    --exclude=.git --exclude=.venv --exclude=working --exclude=models --exclude=dokku --exclude=Dockerfile \
    --exclude=.idea --exclude=.pytest_cache --exclude=.ruff_cache --exclude=__pycache__ \
    -cf - . | tar -x -C "${build_dir}/app"
cp "${PROJECT_DIR}/Dockerfile" "${build_dir}/Dockerfile"
readonly LAB_COMMAND="flyte run --local /app/app.py lab --config /app/config.yaml --project /workspace/$(basename "${PROJECT_DIR}")"
python3 - "${SCHEDULE}" "${LAB_COMMAND}" >"${build_dir}/app.json" <<'PYTHON'
import json
import sys

print(json.dumps({"cron": [{"command": sys.argv[2], "schedule": sys.argv[1]}]}, indent=2))
PYTHON
sed -i "s/^  release: .*$/  release: ${release}/" "${build_dir}/app/config.yaml"
grep -q "^  release: ${release}$" "${build_dir}/app/config.yaml"

git -C "${build_dir}" init --quiet --initial-branch=main
git -C "${build_dir}" add --all --force
git -C "${build_dir}" add --force app/config.yaml "app/roms/${GAME}.nes"
git -C "${build_dir}" commit --quiet --message "Deploy ${APP} ${release} with retro-speedlab-core $(git -C "${CORE_DIR}" rev-parse --short HEAD)"
GIT_SSH_COMMAND="ssh -o ServerAliveInterval=30" git -C "${build_dir}" push --force "${DOKKU_HOST}:${APP}" main
ssh "${DOKKU_HOST}" config:set --no-restart "${APP}" RELEASE="${release}"
echo "Deployed ${APP} ${release}"
