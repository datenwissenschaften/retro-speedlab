$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (Get-Command poetry -ErrorAction SilentlyContinue) {
    poetry install
    & poetry run python app.py
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 app.py
    exit $LASTEXITCODE
}

& python app.py
exit $LASTEXITCODE
