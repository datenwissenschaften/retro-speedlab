#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${PROJECT_DIR}/dokku/settings.sh"
readonly DOKKU_HOST="$(setting dokku.host)"
readonly APP="$(setting dokku.app)"
readonly SCHEDULE="$(setting agent.schedule)"
readonly TODAY="$(date -u +%Y.%m.%d)"

if ! git -C "${PROJECT_DIR}" diff --quiet HEAD; then
    echo "Commit your changes before deploying." >&2
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
git -C "${PROJECT_DIR}" ls-files -z | tar -C "${PROJECT_DIR}" --null -T - -cf - | tar -x -C "${build_dir}"
cp "${PROJECT_DIR}/config.yaml" "${build_dir}/config.yaml"
cp -R "${PROJECT_DIR}/roms/." "${build_dir}/roms/"
sed -i "s/^  release: .*$/  release: ${release}/" "${build_dir}/config.yaml"
python3 - "${SCHEDULE}" "/workspace/$(basename "${PROJECT_DIR}")/agent/daily.sh" >"${build_dir}/app.json" <<'PYTHON'
import json
import sys

print(json.dumps({"cron": [{"command": sys.argv[2], "schedule": sys.argv[1]}]}, indent=2))
PYTHON

git -C "${build_dir}" init --quiet --initial-branch=main
git -C "${build_dir}" add --all --force
git -C "${build_dir}" commit --quiet --message "Deploy ${APP} ${release}"
git -C "${build_dir}" push --force "${DOKKU_HOST}:${APP}" main
ssh "${DOKKU_HOST}" config:set --no-restart "${APP}" RELEASE="${release}"
echo "Deployed ${APP} as ${release}"
