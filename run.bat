@echo off
setlocal
cd /d "%~dp0"
title BioNeMo Agentic Scientist - Local Cockpit

if not exist .venv\Scripts\python.exe (
    echo ======================================================================
    echo   First-time run detected. Launching automated environment setup...
    echo ======================================================================
    if exist scripts\installers\install.bat (
        call scripts\installers\install.bat
    ) else (
        echo [ERROR] Installer not found. Please install dependencies with: py -3 -m pip install -e .
        pause
        exit /b 1
    )
    exit /b
)

echo ======================================================================
echo   NVIDIA BioNeMo ^& NIM Inference Benchmark — Local Workstation
echo   Mode: Unlimited Discovery Active (No Trial Limits)
echo   URL:  http://localhost:8000/cockpit.html
echo ======================================================================
.venv\Scripts\python.exe serve_cockpit.py --open
pause
