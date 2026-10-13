#!/usr/bin/env bash
set -euo pipefail

echo "=============================================================================="
echo "  JORWAL NIM — Autonomous AI Drug Discovery Platform"
echo "  Universal Unix / macOS Installer & Launcher"
echo "=============================================================================="
echo

# 1. Determine Working Directory
if [ -f "serve_cockpit.py" ]; then
    PROJECT_DIR="$(pwd)"
    echo "[1/5] Running inside JORWAL NIM repository: $PROJECT_DIR"
elif [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "$(dirname "${BASH_SOURCE[0]}")/serve_cockpit.py" ]; then
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$PROJECT_DIR"
    echo "[1/5] Running inside JORWAL NIM directory: $PROJECT_DIR"
else
    PROJECT_DIR="${HOME}/jorwal-nim"
    echo "[1/5] Standalone installer detected."
    echo "      Target directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"

    if [ ! -f "serve_cockpit.py" ]; then
        echo "      Fetching JORWAL NIM codebase..."
        if command -v git >/dev/null 2>&1; then
            echo "      Cloning repository via Git..."
            git clone https://github.com/Jorwalzzz/bionemo-nim-benchmark.git "$PROJECT_DIR" 2>/dev/null || \
            git clone https://github.com/Jorwalzzz/bionemo-agentic-scientist.git "$PROJECT_DIR"
        else
            echo "      Downloading repository archive..."
            TMP_ZIP="$(mktemp /tmp/jorwal-nim.XXXXXX.zip)"
            TMP_EXTRACT="$(mktemp -d /tmp/jorwal-ext.XXXXXX)"
            curl -sSL "https://github.com/Jorwalzzz/bionemo-nim-benchmark/archive/refs/heads/main.zip" -o "$TMP_ZIP" || \
            curl -sSL "https://github.com/Jorwalzzz/bionemo-agentic-scientist/archive/refs/heads/main.zip" -o "$TMP_ZIP"
            unzip -q "$TMP_ZIP" -d "$TMP_EXTRACT"
            ROOT_DIR=$(find "$TMP_EXTRACT" -mindepth 1 -maxdepth 1 -type d | head -n 1)
            cp -r "$ROOT_DIR"/* "$PROJECT_DIR/"
            rm -rf "$TMP_ZIP" "$TMP_EXTRACT"
        fi
    fi
fi

if [ ! -f "serve_cockpit.py" ]; then
    echo "[ERROR] Failed to locate or download JORWAL NIM codebase."
    exit 1
fi

# 2. Hardware & Acceleration Probe
echo
echo "[2/5] Probing hardware acceleration..."
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n 1 || true)
    echo "      [GPU] NVIDIA GPU detected: ${GPU_NAME:-Active} (CUDA enabled)"
elif [[ "$(uname)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    echo "      [APPLE] Apple Silicon detected (Metal / MPS accelerated)"
else
    echo "      [CPU] Hardware accelerator not detected. CPU & Mock mode enabled (0 API credits)."
fi

# 3. Python & Virtual Environment Setup
echo
echo "[3/5] Resolving Python 3.10-3.12 runtime..."
HAS_UV=""
if command -v uv >/dev/null 2>&1; then
    HAS_UV=1
elif [ -x "$HOME/.cargo/bin/uv" ]; then
    export PATH="$HOME/.cargo/bin:$PATH"
    HAS_UV=1
elif [ -x "$HOME/.local/bin/uv" ]; then
    export PATH="$HOME/.local/bin:$PATH"
    HAS_UV=1
fi

if [ ! -x ".venv/bin/python" ]; then
    if [ -n "$HAS_UV" ]; then
        echo "      Creating virtual environment via uv (Python 3.12)..."
        uv venv --python 3.12 .venv
    else
        PY=$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3 || command -v python || true)
        if [ -n "$PY" ]; then
            echo "      Creating virtual environment with system Python ($PY)..."
            "$PY" -m venv .venv 2>/dev/null || true
        fi

        if [ ! -x ".venv/bin/python" ]; then
            echo "      Bootstrapping Astral uv runtime manager..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
            if command -v uv >/dev/null 2>&1; then
                HAS_UV=1
                echo "      Provisioning standalone Python 3.12 via uv..."
                uv venv --python 3.12 .venv
            fi
        fi
    fi
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "[ERROR] No Python 3.10+ runtime found. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "      Python environment verified: $(.venv/bin/python --version)"

# 4. Dependency Installation
echo
echo "[4/5] Checking biocompute dependencies..."
if ! cmp -s requirements.txt .venv/requirements.done 2>/dev/null; then
    echo "      Installing dependencies from requirements.txt..."
    if [ -n "$HAS_UV" ]; then
        uv pip install --python .venv/bin/python -q -r requirements.txt
    else
        .venv/bin/python -m pip install -q -r requirements.txt
    fi
    cp requirements.txt .venv/requirements.done
    echo "      Dependencies successfully installed."
else
    echo "      Dependencies up-to-date (cached)."
fi

# 5. Local Configuration & Launch
if [ ! -f ".env" ]; then
    printf 'USE_MOCK=true\nDISABLE_TRIAL_LIMIT=true\nNVIDIA_API_KEY=\n' > .env
    echo "      Generated local .env config."
fi

# Quick launcher script
cat << 'EOF' > run.sh
#!/usr/bin/env bash
cd "$(dirname "$0")"
exec .venv/bin/python serve_cockpit.py --port 8000 --open
EOF
chmod +x run.sh

echo
echo "=============================================================================="
echo "  [5/5] Launching JORWAL NIM Cockpit!"
echo "  Local Address: http://localhost:8000"
echo "  Quick Launcher: ./run.sh"
echo "=============================================================================="
echo

exec .venv/bin/python serve_cockpit.py --port 8000 --open
