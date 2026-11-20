"""
Hermetic Security Tests for Machine-Bound Localhost Owner Access Mode.
Covers hardware MachineGuid verification, strict loopback gating, scrypt password checks,
lockout after 5 failed attempts, and unlimited trial bypass.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.infra.owner_security import (
    OWNER_COOKIE_NAME,
    apply_strict_file_acls,
    get_machine_guid_fingerprint,
    hash_password,
    owner_security_manager,
    sign_session_token,
)
from bionemo_benchmark.server.app import app
from scripts.setup_owner_access import provision_owner_credentials

TEST_OWNER_ID = "laptop_owner"
TEST_OWNER_PASS = "SuperSecretOwnerPassword123!"
TEST_MACHINE_GUID = "guid-win11-precision-9999-alpha"


@pytest.fixture
def owner_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Provisions a hermetic owner_auth.json environment bound to a test MachineGuid."""
    auth_file = tmp_path / "owner_auth.json"
    guid_hash = hashlib.sha256(TEST_MACHINE_GUID.encode("utf-8")).hexdigest()
    salt_hex, hash_hex = hash_password(TEST_OWNER_PASS)
    signing_key = secrets.token_hex(32)

    config = {
        "owner_id": TEST_OWNER_ID,
        "machine_guid_hash": guid_hash,
        "salt_hex": salt_hex,
        "scrypt_hash_hex": hash_hex,
        "signing_key_hex": signing_key,
    }

    with open(auth_file, "w", encoding="utf-8") as f:
        json.dump(config, f)

    apply_strict_file_acls(auth_file)

    monkeypatch.setenv("BIONEMO_MACHINE_GUID", TEST_MACHINE_GUID)
    monkeypatch.setenv("BIONEMO_OWNER_AUTH_PATH", str(auth_file))

    # Reset in-memory rate limiter state
    owner_security_manager.rate_limiter._failures.clear()
    owner_security_manager.rate_limiter._lockouts.clear()

    return {
        "file": auth_file,
        "guid": TEST_MACHINE_GUID,
        "guid_hash": guid_hash,
        "signing_key": signing_key,
        "owner_id": TEST_OWNER_ID,
        "password": TEST_OWNER_PASS,
    }


def test_owner_status_unconfigured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """When owner_auth.json does not exist, status reports configured: false."""
    non_existent = tmp_path / "does_not_exist.json"
    monkeypatch.setenv("BIONEMO_OWNER_AUTH_PATH", str(non_existent))
    client = TestClient(app, client=("127.0.0.1", 54321))
    resp = client.get("/api/owner/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["authenticated"] is False
    assert data["unlimited_trials"] is False


def test_owner_status_non_loopback(owner_env):
    """Non-loopback caller receives 403 Forbidden on status endpoint."""
    client = TestClient(app, client=("192.168.1.100", 54321))
    resp = client.get("/api/owner/status")
    assert resp.status_code == 403
    assert resp.json()["error"] == "LOOPBACK_REQUIRED"


def test_owner_login_success(owner_env):
    """Valid loopback login sets HttpOnly cookie and activates unlimited trials."""
    client = TestClient(app, client=("127.0.0.1", 54321))
    login_resp = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["success"] is True
    assert login_resp.json()["unlimited_trials"] is True
    assert OWNER_COOKIE_NAME in login_resp.cookies

    # Status check with cookie active
    status_resp = client.get("/api/owner/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["configured"] is True
    assert data["authenticated"] is True
    assert data["owner_id"] == TEST_OWNER_ID
    assert data["unlimited_trials"] is True


def test_owner_login_wrong_password(owner_env):
    """Wrong password returns 401 Unauthorized."""
    client = TestClient(app, client=("127.0.0.1", 54321))
    resp = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": "WrongPassword999!"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "INVALID_CREDENTIALS"


def test_owner_lockout_after_5_failures(owner_env):
    """5 consecutive failed login attempts trigger 429 lockout."""
    client = TestClient(app, client=("127.0.0.1", 54321))

    for i in range(4):
        resp = client.post(
            "/api/owner/login",
            json={"owner_id": TEST_OWNER_ID, "password": f"BadPassword{i}"},
        )
        assert resp.status_code == 401

    # 5th attempt triggers lockout
    resp5 = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": "BadPassword5"},
    )
    assert resp5.status_code == 429
    assert resp5.json()["error"] == "OWNER_LOCKOUT"
    assert resp5.json()["retry_after"] > 0

    # Even correct password is now blocked during lockout window
    resp_locked = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )
    assert resp_locked.status_code == 429
    assert resp_locked.json()["error"] == "OWNER_LOCKOUT"


def test_owner_login_non_loopback_rejected(owner_env):
    """Non-loopback client IP is immediately rejected with 403 Forbidden."""
    client = TestClient(app, client=("192.168.1.50", 54321))
    resp = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "LOOPBACK_REQUIRED"


def test_owner_mismatched_machine_guid_rejected(owner_env, monkeypatch: pytest.MonkeyPatch):
    """If owner_auth.json is copied to another machine, mismatched MachineGuid triggers 403."""
    # Simulate moving the file to another computer with different MachineGuid
    monkeypatch.setenv("BIONEMO_MACHINE_GUID", "different-laptop-guid-7777")

    client = TestClient(app, client=("127.0.0.1", 54321))
    resp = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "OWNER_CONFIG_INVALID"


def test_owner_missing_auth_file_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Missing auth file fails closed with 403 Forbidden on login."""
    monkeypatch.setenv("BIONEMO_OWNER_AUTH_PATH", str(tmp_path / "non_existent.json"))
    monkeypatch.setenv("BIONEMO_MACHINE_GUID", TEST_MACHINE_GUID)

    client = TestClient(app, client=("127.0.0.1", 54321))
    resp = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "OWNER_CONFIG_INVALID"


def test_owner_logout(owner_env):
    """Logout clears the owner session cookie and resets status."""
    client = TestClient(app, client=("127.0.0.1", 54321))
    client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )

    logout_resp = client.post("/api/owner/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # After logout, status shows unauthenticated
    status_resp = client.get("/api/owner/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["authenticated"] is False


def test_owner_trial_bypass_in_gate_run(owner_env):
    """Authenticated owner on loopback bypasses researcher login and daily trial quotas."""
    client = TestClient(app, client=("127.0.0.1", 54321))

    # Without owner login, trial status returns standard limits
    t1 = client.get("/api/trial-status")
    assert t1.status_code == 200
    assert t1.json().get("is_owner") is not True

    # Log in as owner
    login_resp = client.post(
        "/api/owner/login",
        json={"owner_id": TEST_OWNER_ID, "password": TEST_OWNER_PASS},
    )
    assert login_resp.status_code == 200

    # Trial status now reflects unlimited owner workstation mode
    t2 = client.get("/api/trial-status")
    assert t2.status_code == 200
    data = t2.json()
    assert data["is_owner"] is True
    assert data["unlimited_trials"] is True
    assert data["role"] == "owner"
    assert data["runs_remaining"] == 999999


def test_setup_owner_access_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Tests the one-time setup CLI provisioning workflow."""
    custom_target = tmp_path / "cli_owner_auth.json"
    monkeypatch.setenv("BIONEMO_MACHINE_GUID", "cli-test-guid-8888")

    exit_code = provision_owner_credentials(
        owner_id="cli_user",
        password="MySecureCliPassword123!",
        target_path=custom_target,
    )

    assert exit_code == 0
    assert custom_target.is_file()

    with open(custom_target, "r", encoding="utf-8") as f:
        record = json.load(f)

    assert record["owner_id"] == "cli_user"
    assert len(record["salt_hex"]) == 32  # 16 bytes hex
    assert len(record["scrypt_hash_hex"]) == 128  # 64 bytes hex
    assert len(record["signing_key_hex"]) == 64  # 32 bytes hex
    expected_guid = hashlib.sha256("cli-test-guid-8888".encode("utf-8")).hexdigest()
    assert record["machine_guid_hash"] == expected_guid
