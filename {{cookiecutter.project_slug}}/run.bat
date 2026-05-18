@echo off
setlocal

cd /d "%~dp0"

where poetry >nul 2>nul
if %errorlevel% equ 0 (
    poetry install
    poetry run python app.py
    exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 app.py
    exit /b %errorlevel%
)

python app.py
exit /b %errorlevel%
