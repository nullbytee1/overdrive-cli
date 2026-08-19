#!/usr/bin/env bash
# OVERDRIVE - Unix / Linux / macOS Launcher

set -e
cd "$(dirname "$0")"

echo -e "\033[1;35m[OVERDRIVE]\033[0m Initializing Python environment..."

if [ ! -d ".venv" ]; then
    echo -e "\033[1;36m[OVERDRIVE]\033[0m Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

python3 overdrive.py
