<#
.SYNOPSIS
    JORWAL NIM — Universal PowerShell 1-Click Installer & Launcher
    Compatible with Windows PowerShell 5.1 and PowerShell 7+
#>

[CmdletBinding()]
param(
    [string]$InstallDir = "$env:USERPROFILE\jorwal-nim",
    [int]$Port = 8000,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Write-Step {
    param([string]$Num, [string]$Title)
    Write-Host "`n[$Num] " -ForegroundColor Cyan -NoNewline
    Write-Host $Title -ForegroundColor White
}

function Write-Success {
    param([string]$Msg)
    Write-Host "      ✓ $Msg" -ForegroundColor Green
}

function Write-Info {
    param([string]$Msg)
    Write-Host "      ℹ $Msg" -ForegroundColor DarkGray
}

Clear-Host
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  JORWAL NIM — Autonomous AI Drug Discovery Platform" -ForegroundColor Cyan
Write-Host "  Universal PowerShell Installer & Local Launcher" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Green

# 1. Determine Workspace Directory
Write-Step "1/5" "Determining installation directory..."

$CurrentDir = $PSScriptRoot
if (-not $CurrentDir -and (Test-Path "serve_cockpit.py")) {
    $CurrentDir = (Get-Location).Path
}

if ($CurrentDir -and (Test-Path (Join-Path $CurrentDir "serve_cockpit.py"))) {
    $TargetDir = $CurrentDir
    Set-Location $TargetDir
    Write-Success "Running inside existing JORWAL NIM repository: $TargetDir"
} else {
    $TargetDir = $InstallDir
    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }
    Set-Location $TargetDir
    Write-Info "Target directory: $TargetDir"

    if (-not (Test-Path (Join-Path $TargetDir "serve_cockpit.py"))) {
        Write-Info "Downloading JORWAL NIM codebase..."
        $HasGit = Get-Command git -ErrorAction SilentlyContinue
        if ($HasGit) {
            Write-Info "Cloning via git..."
            try {
                git clone https://github.com/Jorwalzzz/bionemo-nim-benchmark.git $TargetDir
            } catch {
                git clone https://github.com/Jorwalzzz/bionemo-agentic-scientist.git $TargetDir
            }
        } else {
            Write-Info "Git not detected. Downloading package zip archive..."
            $ZipPath = Join-Path $env:TEMP "jorwal-nim.zip"
            $ExtractPath = Join-Path $env:TEMP "jorwal-nim-extract"
            try {
                Invoke-WebRequest -Uri "https://github.com/Jorwalzzz/bionemo-nim-benchmark/archive/refs/heads/main.zip" -OutFile $ZipPath -UseBasicParsing
            } catch {
                Invoke-WebRequest -Uri "https://github.com/Jorwalzzz/bionemo-agentic-scientist/archive/refs/heads/main.zip" -OutFile $ZipPath -UseBasicParsing
            }
            Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force
            $SubFolder = Get-ChildItem -Path $ExtractPath | Where-Object { $_.PSIsContainer } | Select-Object -First 1
            Copy-Item -Path "$($SubFolder.FullName)\*" -Destination $TargetDir -Recurse -Force
            Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
            Remove-Item $ExtractPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Success "Repository files ready at: $TargetDir"
}

# 2. Hardware & CUDA Probe
Write-Step "2/5" "Probing hardware acceleration..."
$NvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($NvidiaSmi) {
    try {
        $GpuName = (& nvidia-smi --query-gpu=name --format=csv,noheader)[0].Trim()
        Write-Success "NVIDIA GPU Detected: $GpuName (CUDA Accelerated)"
    } catch {
        Write-Info "NVIDIA driver found; CUDA ready."
    }
} else {
    Write-Info "NVIDIA GPU not detected. High-efficiency CPU & Mock mode enabled (0 API cost)."
}

# 3. Python & Virtual Environment Setup
Write-Step "3/5" "Configuring isolated Python environment..."

# Check Astral uv
$UvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $UvCmd -and (Test-Path "$env:USERPROFILE\.cargo\bin\uv.exe")) {
    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    $UvCmd = Get-Command uv -ErrorAction SilentlyContinue
}
if (-not $UvCmd -and (Test-Path "$env:LOCALAPPDATA\uv\uv.exe")) {
    $env:PATH = "$env:LOCALAPPDATA\uv;$env:PATH"
    $UvCmd = Get-Command uv -ErrorAction SilentlyContinue
}

$VenvPython = Join-Path $TargetDir ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    if ($UvCmd) {
        Write-Info "Creating virtual environment using uv (Python 3.12)..."
        & uv venv --python 3.12 (Join-Path $TargetDir ".venv")
    } else {
        # Try system Python
        $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
        $PyCmd = Get-Command python -ErrorAction SilentlyContinue

        $Created = $false
        if ($PyLauncher) {
            Write-Info "Trying Python launcher (py -3)..."
            try {
                & py -3.12 -m venv (Join-Path $TargetDir ".venv") 2>$null
                if (Test-Path $VenvPython) { $Created = $true }
            } catch {}
            if (-not $Created) {
                try {
                    & py -3 -m venv (Join-Path $TargetDir ".venv") 2>$null
                    if (Test-Path $VenvPython) { $Created = $true }
                } catch {}
            }
        }

        if (-not $Created -and $PyCmd) {
            Write-Info "Trying system python -m venv..."
            try {
                & python -m venv (Join-Path $TargetDir ".venv") 2>$null
                if (Test-Path $VenvPython) { $Created = $true }
            } catch {}
        }

        if (-not $Created) {
            Write-Info "Bootstrapping Astral uv package manager for autonomous Python 3.12..."
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
            if (Test-Path "$env:USERPROFILE\.cargo\bin\uv.exe") {
                $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
            }
            if (Test-Path "$env:LOCALAPPDATA\uv\uv.exe") {
                $env:PATH = "$env:LOCALAPPDATA\uv;$env:PATH"
            }
            $UvCmd = Get-Command uv -ErrorAction SilentlyContinue
            if ($UvCmd) {
                Write-Info "Provisioning standalone Python 3.12 runtime..."
                & uv venv --python 3.12 (Join-Path $TargetDir ".venv")
            }
        }
    }
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "`n[ERROR] Could not initialize Python virtual environment." -ForegroundColor Red
    Write-Host "Please install Python 3.10-3.12 from https://www.python.org/downloads/ or run:" -ForegroundColor Yellow
    Write-Host "irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Yellow
    exit 1
}

$PyVer = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Success "Active Python environment: Python $PyVer"

# 4. Dependency Installation
Write-Step "4/5" "Verifying biocompute dependencies..."
$ReqFile = Join-Path $TargetDir "requirements.txt"
$DoneFile = Join-Path $TargetDir ".venv\requirements.done"

$NeedsInstall = $true
if ((Test-Path $DoneFile) -and (Test-Path $ReqFile)) {
    $Hash1 = (Get-FileHash $ReqFile -Algorithm SHA256).Hash
    $Hash2 = (Get-FileHash $DoneFile -Algorithm SHA256).Hash
    if ($Hash1 -eq $Hash2) {
        $NeedsInstall = $false
    }
}

if ($NeedsInstall) {
    Write-Info "Installing dependencies from requirements.txt (RDKit, FastAPI, BioNeMo)..."
    if ($UvCmd) {
        & uv pip install --python $VenvPython -q -r $ReqFile
    } else {
        & $VenvPython -m pip install -q -r $ReqFile
    }
    Copy-Item -Path $ReqFile -Destination $DoneFile -Force
    Write-Success "Dependencies installed and cached."
} else {
    Write-Success "Dependencies verified (cached)."
}

# 5. Local Configuration & Shortcuts
Write-Step "5/5" "Configuring local environment & desktop shortcuts..."
$EnvFile = Join-Path $TargetDir ".env"
if (-not (Test-Path $EnvFile)) {
    @"
# JORWAL NIM - Local Configuration
USE_MOCK=true
DISABLE_TRIAL_LIMIT=true
NVIDIA_API_KEY=
"@ | Out-File -FilePath $EnvFile -Encoding utf8
    Write-Success "Created default .env (Mock Mode enabled, zero-credit required)"
}

# Write launcher bat
$RunBat = Join-Path $TargetDir "run.bat"
@"
@echo off
cd /d "%~dp0"
title JORWAL NIM Cockpit
echo Starting JORWAL NIM Cockpit...
.venv\Scripts\python.exe serve_cockpit.py --port $Port --open
pause
"@ | Out-File -FilePath $RunBat -Encoding ascii

# Create Desktop Shortcut
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $DesktopPath = [Environment]::GetFolderPath('Desktop')
    $Shortcut = $WshShell.CreateShortcut((Join-Path $DesktopPath "JORWAL NIM Cockpit.lnk"))
    $Shortcut.TargetPath = $RunBat
    $Shortcut.WorkingDirectory = $TargetDir
    $Shortcut.Description = "Launch JORWAL NIM AI Drug Discovery Cockpit"
    $Shortcut.Save()
    Write-Success "Created Desktop shortcut: 'JORWAL NIM Cockpit'"
} catch {
    Write-Info "Desktop shortcut skipped."
}

# Launch Cockpit
Write-Host "`n==============================================================================" -ForegroundColor Green
Write-Host "  Setup Complete! Launching JORWAL NIM Cockpit..." -ForegroundColor Cyan
Write-Host "  URL: http://localhost:$Port" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Green

$OpenArg = if ($NoBrowser) { "" } else { "--open" }
& $VenvPython (Join-Path $TargetDir "serve_cockpit.py") --port $Port $OpenArg
