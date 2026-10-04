@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo   JORWALZZZ BioNeMo Agentic Scientist - 1-Click Secure Local Setup
echo ======================================================================
echo [1/5] Checking Python installation...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    py -3 --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python 3.10+ is required but was not found on your PATH.
        echo Please download and install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    ) else (
        set "PY_CMD=py -3"
    )
) else (
    set "PY_CMD=python"
)

echo [2/5] Creating dedicated local virtual environment (.venv)...
if not exist ".venv" (
    %PY_CMD% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/5] Installing verified scientific dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some optional packages failed to install, proceeding with core engine...
)

echo [4/5] Initializing local client configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Created .env configured for unlimited local offline execution (USE_MOCK=true, DISABLE_TRIAL_LIMIT=true).
    ) else (
        (
            echo DISABLE_TRIAL_LIMIT=true
            echo USE_MOCK=true
            echo NVIDIA_API_KEY=
        ) > .env
    )
)

echo [5/5] Launching JORWALZZZ BioNeMo Cockpit on http://localhost:8000 ...
echo ======================================================================
echo   * Unmetered Local Execution Enabled (No Trial Restrictions)
echo   * Zero Telemetry - 100%% Private & Hermetic Local Execution
echo   * Press Ctrl+C in this terminal window to stop the server
echo ======================================================================

start http://localhost:8000
python serve_cockpit.py --port 8000

pause
