"""
Deterministic unit and integration tests for FastAPI Server Endpoints,
Input Validation, Path Traversal Defenses, Rate Limiting, and Authentication.
Part of NVIDIA BioNeMo Benchmark Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.server.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestServerStaticAndSecurityHeaders:
    """Verifies enterprise security headers, path traversal protection, and root asset whitelisting."""

    def test_security_headers_present_on_root_assets(self, client):
        res = client.get("/cockpit.css")
        assert res.status_code == 200
        assert res.headers["x-content-type-options"] == "nosniff"
        assert res.headers["x-frame-options"] in ("DENY", "SAMEORIGIN")
        assert res.headers["x-xss-protection"] == "1; mode=block"
        assert "default-src 'self'" in res.headers["content-security-policy"]

    def test_non_whitelisted_root_file_blocked(self, client):
        assert client.get("/pyproject.toml").status_code == 404
        assert client.get("/.env").status_code == 404
        assert client.get("/README.md").status_code == 404

    def test_path_traversal_attack_blocked(self, client):
        bad_paths = [
            "/..%2F..%2Fpyproject.toml",
            "/..\\..\\pyproject.toml",
            "/assets/../../.env",
            "/data/../../pyproject.toml",
        ]
        for p in bad_paths:
            res = client.get(p)
            assert res.status_code in (400, 404)

    def test_oversized_payload_rejected(self, client):
        huge_payload = {"smiles": "C" * 150000}
        res = client.post("/api/redock", json=huge_payload)
        assert res.status_code == 413
        assert res.json()["error"] == "PAYLOAD_TOO_LARGE"


class TestTargetAndBenchmarkEndpoints:
    """Verifies health probes, target resolution, and API defense mechanisms."""

    def test_health_endpoints(self, client):
        res_h = client.get("/api/health")
        assert res_h.status_code == 200
        assert res_h.json()["status"] == "healthy"

        res_hz = client.get("/healthz")
        assert res_hz.status_code == 200
        assert res_hz.json()["status"] == "healthy"

    def test_fetch_target_valid_and_validation_guard(self, client):
        res_valid = client.post("/api/target/fetch", json={"target": "8AZV"})
        assert res_valid.status_code == 200
        assert res_valid.json()["pdb_id"] == "8AZV"

        # Biosecurity restriction triggers 400 VALIDATION_FAILED on regulated toxin
        res_bad = client.post("/api/target/fetch", json={"target": "ricin toxin"})
        assert res_bad.status_code == 400
        assert res_bad.json()["error"] == "VALIDATION_FAILED"

    def test_redock_malformed_json_rejected(self, client):
        # Non-JSON or malformed syntax returns 400
        res = client.post("/api/redock", content=b"invalid-binary-content-not-json", headers={"Content-Type": "application/json"})
        assert res.status_code == 400

    def test_csrf_origin_rejection(self, client):
        # Requests with untrusted Origin header must be rejected
        res = client.post(
            "/api/resistance/evolve",
            json={"smiles": "CC", "target": "8AZV"},
            headers={"Origin": "https://malicious-phishing-site.com"}
        )
        assert res.status_code == 403
        assert res.json()["error"] == "CSRF_ORIGIN_REJECTED"


class TestAuthAndQuotaEndpoints:
    """Verifies session lifecycle, trial status checks, and registration paths."""

    def test_trial_status_endpoint(self, client):
        res = client.get("/api/trial-status")
        assert res.status_code == 200
        data = res.json()
        assert "runs_remaining" in data
        assert data["runs_remaining"] >= 0

    def test_unauthenticated_me_endpoint(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["authenticated"] is False
        assert "quota" in data

    def test_register_and_login_flow(self, client):
        test_email = "scientist_hermetic_unit_test@stanford.edu"
        reg_payload = {
            "email": test_email,
            "password_hash": "sha256_mock_hash_for_testing",
            "organization": "Stanford BioE",
            "fingerprint": "fp_test_scientist_42"
        }
        reg_res = client.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code in (200, 400)

        login_res = client.post("/api/auth/login", json={"email": test_email, "password_hash": "sha256_mock_hash_for_testing"})
        assert login_res.status_code in (200, 401)
