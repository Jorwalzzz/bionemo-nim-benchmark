"""
Unit and Integration Tests for JORWAL NIM Redesigned Universal Installers.
Validates install.bat, install.ps1, install.sh, download endpoints, and checksum integrity.
"""

import os
from fastapi.testclient import TestClient
from serve_cockpit import app

client = TestClient(app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_install_bat_content_and_invariants():
    bat_path = os.path.join(BASE_DIR, "scripts", "installers", "install.bat")
    assert os.path.exists(bat_path), "install.bat must exist"
    with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "BioNeMo Agentic Scientist" in content
    assert "serve_cockpit.py" in content
    assert "venv" in content
    assert "http://localhost:8000" in content


def test_install_ps1_content_and_invariants():
    ps1_path = os.path.join(BASE_DIR, "scripts", "installers", "install.ps1")
    assert os.path.exists(ps1_path), "install.ps1 must exist"
    with open(ps1_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "JORWAL NIM" in content
    assert "serve_cockpit.py" in content
    assert "nvidia-smi" in content
    assert "uv venv --python 3.12" in content
    assert "pip install" in content
    assert "pyproject.toml" in content
    assert "JORWAL NIM Cockpit.lnk" in content


def test_install_sh_content_and_invariants():
    sh_path = os.path.join(BASE_DIR, "scripts", "installers", "install.sh")
    assert os.path.exists(sh_path), "install.sh must exist"
    with open(sh_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    assert "BioNeMo Agentic Scientist" in content
    assert "serve_cockpit.py" in content
    assert "venv" in content
    assert "http://localhost:8000" in content


def test_installer_api_endpoints():
    # Windows installer endpoint (serves install.bat text)
    resp_win = client.get("/api/download/installer-windows")
    assert resp_win.status_code == 200
    assert "BioNeMo Agentic Scientist" in resp_win.text
    assert "attachment; filename=install.bat" in resp_win.headers.get("content-disposition", "")

    # Dedicated setup-exe endpoint (transparently serves install.bat for zero-binary security)
    resp_exe = client.get("/api/download/setup-exe")
    assert resp_exe.status_code == 200
    assert "attachment; filename=install.bat" in resp_exe.headers.get("content-disposition", "")

    # Unix SH endpoint
    resp_sh = client.get("/api/download/installer-unix")
    assert resp_sh.status_code == 200
    assert "BioNeMo Agentic Scientist" in resp_sh.text
    assert "attachment; filename=install.sh" in resp_sh.headers.get("content-disposition", "")

    # PowerShell PS1 endpoint
    resp_ps = client.get("/api/download/installer-powershell")
    assert resp_ps.status_code == 200
    assert "JORWAL NIM" in resp_ps.text
    assert "attachment; filename=install.ps1" in resp_ps.headers.get("content-disposition", "")


def test_checksums_includes_all_installers():
    resp = client.get("/api/download/checksums")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "install.bat" in data["checksums"]
    assert "install.sh" in data["checksums"]
    assert "install.ps1" in data["checksums"]
    assert "InstallerWizard.cs" in data["checksums"]
    assert "pyproject.toml" in data["checksums"]
    assert data["checksums"]["install.bat"] is not None
    assert data["checksums"]["install.sh"] is not None
    assert data["checksums"]["install.ps1"] is not None
    assert data["checksums"]["InstallerWizard.cs"] is not None
    assert data["checksums"]["pyproject.toml"] is not None


def test_setup_guide_endpoint():
    resp = client.get("/api/setup-guide")
    assert resp.status_code == 200
    data = resp.json()
    assert "install.ps1" in data["windows_powershell"]
    assert "install.sh" in data["unix_curl"]
    assert "docker" in data
