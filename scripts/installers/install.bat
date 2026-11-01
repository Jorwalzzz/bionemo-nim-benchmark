@echo off
setlocal
title BioNeMo Agentic Scientist - Local Setup
set "ZIP_URL=https://github.com/Jorwalzzz/bionemo-nim-benchmark/archive/refs/heads/main.zip"

echo ======================================================================
echo   JORWAL NIM — BioNeMo Agentic Scientist - Local Offline Setup
echo ======================================================================

echo [1/5] Checking Python...
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo [ERROR] Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" in the installer, then run this file again.
    goto :fail
)

echo [2/5] Getting project files...
if exist serve_cockpit.py goto :have_files
if exist ..\..\serve_cockpit.py (
    cd /d ..\..
    goto :have_files
)
if exist bionemo-local\serve_cockpit.py goto :enter_dir
echo Downloading from GitHub...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%ZIP_URL%' -OutFile bionemo.zip; Expand-Archive bionemo.zip -DestinationPath bionemo-tmp -Force"
if errorlevel 1 (
    echo [ERROR] Download failed. Check your internet connection and try again.
    goto :fail
)
move bionemo-tmp\bionemo-nim-benchmark-main bionemo-local >nul
del bionemo.zip
rmdir /s /q bionemo-tmp
:enter_dir
cd /d bionemo-local
:have_files

echo [3/5] Creating virtual environment...
if not exist .venv\Scripts\python.exe %PY% -m venv .venv
if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    goto :fail
)

echo [4/5] Installing packages. This can take a few minutes, please wait...
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -e .
if errorlevel 1 (
    echo [ERROR] Package install failed. Scroll up to see which package failed.
    goto :fail
)

if not exist .env (
    echo DISABLE_TRIAL_LIMIT=true> .env
    echo USE_MOCK=true>> .env
    echo NVIDIA_API_KEY=>> .env
)

if not exist run.bat (
    echo @echo off> run.bat
    echo cd /d "%%~dp0">> run.bat
    echo title BioNeMo Discovery Cockpit>> run.bat
    echo .venv\Scripts\python.exe serve_cockpit.py --open>> run.bat
    echo pause>> run.bat
)

if "%~1"=="--setup-wizard" (
    echo Setup completed for wizard.
    exit /b 0
)

echo [5/5] Starting the cockpit at http://localhost:8000/cockpit.html
echo Keep this window open. Press Ctrl+C to stop.
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000/cockpit.html"
.venv\Scripts\python.exe serve_cockpit.py
echo.
echo The server stopped. See any error above.
goto :fail

:fail
echo.
pause
exit /b 1
