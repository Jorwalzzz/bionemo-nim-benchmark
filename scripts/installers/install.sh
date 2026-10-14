#!/usr/bin/env bash
set -e
ZIP_URL="https://github.com/Jorwalzzz/bionemo-nim-benchmark/archive/refs/heads/main.zip"

echo "== JORWAL NIM — BioNeMo Agentic Scientist - Local Offline Setup =="

echo "[1/5] Checking Python..."
PY=$(command -v python3 || command -v python || true)
[ -n "$PY" ] || { echo "[ERROR] Python 3.10+ not found. Install it and re-run."; exit 1; }

echo "[2/5] Getting project files..."
if [ ! -f "serve_cockpit.py" ]; then
    if [ -f "../../serve_cockpit.py" ]; then
        cd ../..
    elif [ -f "bionemo-local/serve_cockpit.py" ]; then
        cd bionemo-local
    else
        echo "Downloading from GitHub..."
        curl -sSL "$ZIP_URL" -o bionemo.zip
        unzip -q bionemo.zip -d bionemo-tmp
        mv bionemo-tmp/bionemo-nim-benchmark-main bionemo-local
        rm -f bionemo.zip
        rm -rf bionemo-tmp
        cd bionemo-local
    fi
fi

echo "[3/5] Creating virtual environment..."
if [ ! -f ".venv/bin/python" ]; then
    "$PY" -m venv .venv
fi

echo "[4/5] Installing packages..."
.venv/bin/python -m pip install --disable-pip-version-check -e .

if [ ! -f ".env" ]; then
    cat <<EOF > .env
DISABLE_TRIAL_LIMIT=true
USE_MOCK=true
NVIDIA_API_KEY=
EOF
fi

echo "[5/5] Starting cockpit at http://localhost:8000"
echo "Keep this window open. Press Ctrl+C to stop."
(sleep 3 && { command -v xdg-open >/dev/null && xdg-open http://localhost:8000 || open http://localhost:8000 || true; }) &
.venv/bin/python serve_cockpit.py
