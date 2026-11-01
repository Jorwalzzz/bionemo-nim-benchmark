#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
    echo "======================================================================"
    echo "  First-time run detected. Launching automated environment setup..."
    echo "======================================================================"
    if [ -f "scripts/installers/install.sh" ]; then
        bash scripts/installers/install.sh
    else
        echo "[ERROR] Installer not found. Please install dependencies with: python3 -m pip install -e ."
        exit 1
    fi
    exit 0
fi

echo "======================================================================"
echo "  NVIDIA BioNeMo & NIM Inference Benchmark — Local Workstation"
echo "  Mode: Unlimited Discovery Active (No Trial Limits)"
echo "  URL:  http://localhost:8000/cockpit.html"
echo "======================================================================"
.venv/bin/python serve_cockpit.py --open
