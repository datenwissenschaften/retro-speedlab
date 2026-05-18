#!/usr/bin/env sh

set -eu

cd "$(dirname "$0")"

if command -v poetry >/dev/null 2>&1; then
    poetry install
    exec poetry run python app.py
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 app.py
fi

exec python app.py
