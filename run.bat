@echo off
setlocal enabledelayedexpansion
title OVERDRIVE - Enterprise Linux VPS Performance Engine
chcp 65001 >nul

cd /d "%~dp0"

echo [OVERDRIVE] Initializing virtual environment...
if not exist ".venv" (
    echo [OVERDRIVE] Creating Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [OVERDRIVE] Installing required dependencies...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python overdrive.py
pause
