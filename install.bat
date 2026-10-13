@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title JORWAL NIM — Autonomous AI Drug Discovery Platform Installer

echo ==============================================================================
echo   JORWAL NIM — Autonomous AI Drug Discovery Platform
echo   Universal Windows One-Click Installer & Launcher
echo ==============================================================================
echo.

rem ─── 1. Determine Working Directory ──────────────────────────────────────────
set "CURRENT_DIR=%~dp0"
if exist "%CURRENT_DIR%serve_cockpit.py" (
    set "PROJECT_DIR=%CURRENT_DIR%"
    cd /d "%PROJECT_DIR%"
    echo [1/5] Running inside JORWAL NIM workspace:
    echo       %PROJECT_DIR%
) else (
    echo [1/5] Standalone installer detected (outside project directory).
    set "PROJECT_DIR=%USERPROFILE%\jorwal-nim"
    echo       Target directory: !PROJECT_DIR!
    if not exist "!PROJECT_DIR!" mkdir "!PROJECT_DIR!"
    cd /d "!PROJECT_DIR!"

    if not exist "!PROJECT_DIR!\serve_cockpit.py" (
        echo       Fetching JORWAL NIM codebase...
        where git >nul 2>&1
        if not errorlevel 1 (
            echo       Cloning repository via Git...
            git clone https://github.com/Jorwalzzz/bionemo-nim-benchmark.git "!PROJECT_DIR!" 2>nul || git clone https://github.com/Jorwalzzz/bionemo-agentic-scientist.git "!PROJECT_DIR!"
        ) else (
            echo       Git not detected. Downloading package zip via PowerShell...
            powershell -NoProfile -ExecutionPolicy Bypass -Command ^
                "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
                "$zip = Join-Path $env:TEMP 'jorwal-nim.zip'; " ^
                "try { Invoke-WebRequest -Uri 'https://github.com/Jorwalzzz/bionemo-nim-benchmark/archive/refs/heads/main.zip' -OutFile $zip -UseBasicParsing } catch { Invoke-WebRequest -Uri 'https://github.com/Jorwalzzz/bionemo-agentic-scientist/archive/refs/heads/main.zip' -OutFile $zip -UseBasicParsing }; " ^
                "$extract = Join-Path $env:TEMP 'jorwal-extract'; " ^
                "Expand-Archive -Path $zip -DestinationPath $extract -Force; " ^
                "$sub = Get-ChildItem -Path $extract | Where-Object { $_.PSIsContainer } | Select-Object -First 1; " ^
                "Copy-Item -Path \"$($sub.FullName)\*\" -Destination '$env:PROJECT_DIR' -Recurse -Force; " ^
                "Remove-Item $zip -Force -ErrorAction SilentlyContinue; " ^
                "Remove-Item $extract -Recurse -Force -ErrorAction SilentlyContinue;"
        )
    )
)

if not exist "serve_cockpit.py" (
    echo [ERROR] Could not find or download JORWAL NIM files.
    echo Please ensure an internet connection is active or clone manually:
    echo   git clone https://github.com/Jorwalzzz/bionemo-nim-benchmark.git
    echo.
    pause
    exit /b 1
)

rem ─── 2. Hardware & GPU Probe ────────────────────────────────────────────────
echo.
echo [2/5] Probing hardware acceleration...
set "DETECTED_GPU="
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%g in ('nvidia-smi --query-gpu=name --format=csv^,noheader 2^>nul') do (
        if not defined DETECTED_GPU set "DETECTED_GPU=%%g"
    )
)
if defined DETECTED_GPU (
    echo       [GPU] NVIDIA GPU detected: !DETECTED_GPU! (CUDA enabled)
) else (
    echo       [CPU] NVIDIA GPU not detected. High-efficiency CPU & Mock mode enabled.
)

rem ─── 3. Python & Virtual Environment Setup ──────────────────────────────────
echo.
echo [3/5] Resolving Python 3.10-3.12 environment...

set "HAS_UV="
where uv >nul 2>&1 && set "HAS_UV=1"
if not defined HAS_UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "PATH=%USERPROFILE%\.cargo\bin;!PATH!"
    set "HAS_UV=1"
)
if not defined HAS_UV if exist "%LOCALAPPDATA%\uv\uv.exe" (
    set "PATH=%LOCALAPPDATA%\uv;!PATH!"
    set "HAS_UV=1"
)

if not exist ".venv\Scripts\python.exe" (
    if defined HAS_UV (
        echo       Initializing isolated Python 3.12 virtual environment via uv...
        uv venv --python 3.12 .venv
    ) else (
        echo       Checking system Python...
        py -3.12 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || py -3.10 -m venv .venv 2>nul || py -3 -m venv .venv 2>nul || python -m venv .venv 2>nul
        if not exist ".venv\Scripts\python.exe" (
            echo       No compatible Python installation found.
            echo       Auto-bootstrapping high-performance Astral uv package manager...
            powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
            if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "PATH=%USERPROFILE%\.cargo\bin;!PATH!"
            if exist "%LOCALAPPDATA%\uv\uv.exe" set "PATH=%LOCALAPPDATA%\uv;!PATH!"
            where uv >nul 2>&1 && set "HAS_UV=1"
            if defined HAS_UV (
                echo       Provisioning standalone Python 3.12 runtime via uv...
                uv venv --python 3.12 .venv
            )
        )
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Failed to initialize Python virtual environment.
    echo Please install Python 3.10-3.12 from https://www.python.org/downloads/
    echo or install uv via PowerShell: irm https://astral.sh/uv/install.ps1 ^| iex
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('".venv\Scripts\python.exe" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"') do (
    set "PY_VER=%%v"
)
echo       Python environment ready: !PY_VER!

rem ─── 4. Dependencies Installation ──────────────────────────────────────────
echo.
echo [4/5] Checking biocompute dependencies (FastAPI, RDKit, BioNeMo)...
fc /b requirements.txt .venv\requirements.done >nul 2>&1
if errorlevel 1 (
    echo       Installing/updating dependencies from requirements.txt...
    if defined HAS_UV (
        uv pip install --python .venv\Scripts\python.exe -q -r requirements.txt
    ) else (
        .venv\Scripts\python.exe -m pip install -q -r requirements.txt
    )
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed. Check your internet connection.
        echo Retrying in verbose mode...
        .venv\Scripts\python.exe -m pip install -r requirements.txt
        if errorlevel 1 (
            pause
            exit /b 1
        )
    )
    copy /y requirements.txt .venv\requirements.done >nul
    echo       Dependencies successfully installed and verified.
) else (
    echo       Dependencies verified (up-to-date).
)

rem ─── 5. Offline & Security Configuration ───────────────────────────────────
if not exist ".env" (
    (
        echo # JORWAL NIM - Local Configuration
        echo USE_MOCK=true
        echo DISABLE_TRIAL_LIMIT=true
        echo NVIDIA_API_KEY=
    ) > .env
    echo       Generated default .env (Zero-credit mock mode enabled).
)

rem ─── 6. Create Quick Launcher & Desktop Shortcut ───────────────────────────
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo title JORWAL NIM Cockpit
    echo echo Starting JORWAL NIM Cockpit...
    echo .venv\Scripts\python.exe serve_cockpit.py --port 8000 --open
    echo pause
) > run.bat

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
    "$sc = $ws.CreateShortcut((Join-Path $desktop 'JORWAL NIM Cockpit.lnk')); " ^
    "$sc.TargetPath = (Join-Path '%CD%' 'run.bat'); " ^
    "$sc.WorkingDirectory = '%CD%'; " ^
    "$sc.Description = 'Launch JORWAL NIM AI Drug Discovery Cockpit'; " ^
    "$sc.Save()" >nul 2>&1

rem ─── 7. Launch Cockpit ─────────────────────────────────────────────────────
echo.
echo ==============================================================================
echo   [5/5] Launching JORWAL NIM Cockpit!
echo   Local Address: http://localhost:8000
echo   Quick Launcher: run.bat (Desktop shortcut created)
echo ==============================================================================
echo.
if "%1"=="--setup-wizard" (
    echo       [WIZARD] Launching background server for Windows Setup Wizard...
    start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000"
    start "" .venv\Scripts\python.exe serve_cockpit.py --port 8000
    exit /b 0
)

.venv\Scripts\python.exe serve_cockpit.py --port 8000 --open
pause
