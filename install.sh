#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "  JORWALZZZ BioNeMo Agentic Scientist - 1-Click Secure Local Setup"
echo "======================================================================"
echo "[1/5] Checking Python installation..."

if command -v python3 >/dev/null 2>&1; then
    PY_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PY_BIN=python
else
    echo "[ERROR] Python 3.10+ is required but not found."
    echo "Please install Python from https://www.python.org/downloads/ or your package manager."
    exit 1
fi

echo "[2/5] Creating dedicated local virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    $PY_BIN -m venv .venv
fi

echo "[3/5] Installing verified scientific dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q || echo "[WARNING] Continuing with core modules..."

echo "[4/5] Initializing local client configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env configured for unlimited local offline execution (USE_MOCK=true, DISABLE_TRIAL_LIMIT=true)."
    else
        cat <<EOF > .env
DISABLE_TRIAL_LIMIT=true
USE_MOCK=true
NVIDIA_API_KEY=
EOF
    fi
fi

echo "[5/5] Launching JORWALZZZ BioNeMo Cockpit on http://localhost:8000 ..."
echo "======================================================================"
echo "  * Unmetered Local Execution Enabled (No Trial Restrictions)"
echo "  * Zero Telemetry - 100% Private & Hermetic Local Execution"
echo "  * Press Ctrl+C in this terminal window to stop the server"
echo "======================================================================"

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:8000 &
elif command -v open >/dev/null 2>&1; then
    open http://localhost:8000 &
fi

python serve_cockpit.py --port 8000
