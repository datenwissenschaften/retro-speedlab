#!/usr/bin/env bash
set -euo pipefail

readonly PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${PROJECT_DIR}/dokku/settings.sh"
readonly DOKKU_HOST="$(setting dokku.host)"
readonly APP="$(setting dokku.app)"
readonly SCHEDULE="$(setting agent.schedule)"
readonly TODAY="$(date -u +%Y.%m.%d)"
readonly IMAGE_PYTHON="3.12"
readonly IMAGE_PLATFORM="manylinux_2_28_x86_64"

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
python3 - "${PROJECT_DIR}/pyproject.toml" >"${build_dir}/dependencies.txt" <<'PYTHON'
import sys
import tomllib

print("\n".join(tomllib.load(open(sys.argv[1], "rb"))["project"]["dependencies"]))
PYTHON
python3 -m pip download --quiet --no-deps --only-binary=:all: --python-version "${IMAGE_PYTHON}" \
    --platform "${IMAGE_PLATFORM}" --dest "${build_dir}/wheels" --requirement "${build_dir}/dependencies.txt"
python3 - "${build_dir}/wheels" >"${build_dir}/requirements.txt" <<'PYTHON'
import sys
import zipfile
from email.parser import Parser
from pathlib import Path

for wheel in sorted(Path(sys.argv[1]).glob("*.whl")):
    with zipfile.ZipFile(wheel) as archive:
        metadata = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        for key, requirement in Parser().parsestr(archive.read(metadata).decode("utf-8")).items():
            if key == "Requires-Dist" and "extra ==" not in requirement:
                print(requirement)
PYTHON
python3 - "${SCHEDULE}" "/workspace/$(basename "${PROJECT_DIR}")/agent/trigger.sh" >"${build_dir}/app.json" <<'PYTHON'
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
