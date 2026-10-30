#!/usr/bin/env bash
set -euo pipefail

readonly WRAPPER="src.game.wrapper:GameWrapper"
readonly ROUTES="/app/working/cache/tas/levels.msgpack"

ruff check
ruff format --check
python -m pytest -q
if [[ -f "${ROUTES}" ]]; then
    mkdir -p working/cache/tas
    python -m datenwissenschaften.tas.run verify "${WRAPPER}" config.yaml "${ROUTES}"
else
    echo "verify: no level routes at ${ROUTES}; replay skipped" >&2
fi
git rev-parse HEAD >agent/.verified
