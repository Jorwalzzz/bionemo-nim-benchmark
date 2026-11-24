"""
Security Regression Test Suite for BioNeMo NIM Benchmark Suite.
Tests CWE-22 (Path Traversal), CWE-78 (Command Injection), CWE-88 (Argument Injection),
CWE-918 (SSRF), CWE-1236 (CSV Formula Injection), DOM XSS sanitization, and secret leakage defense.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.core.client import NimBioClient
from bionemo_benchmark.core.pipeline import BenchmarkPipeline
from bionemo_benchmark.infra.security_sentinel import SafeSanitizer, SecretScrubber
from bionemo_benchmark.mcp.server import bionemo_fetch_rcsb_pdb, bionemo_run_benchmark
from bionemo_benchmark.server.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestPathTraversalDefense:
    """Verifies CWE-22 Path Traversal prevention on all path inputs."""

    def test_validate_safe_path_blocks_parent_traversal(self, tmp_path):
        base_dir = tmp_path / "sandbox"
        base_dir.mkdir()
        (base_dir / "target.txt").write_text("safe content", encoding="utf-8")

        # Legitimate path
        safe_path = SafeSanitizer.validate_safe_path("target.txt", base_dir)
        assert safe_path.exists()
        assert safe_path.is_relative_to(base_dir.resolve())

        # Traversal attempts
        with pytest.raises(ValueError, match="Path traversal detected"):
            SafeSanitizer.validate_safe_path("../../etc/passwd", base_dir)

        with pytest.raises(ValueError, match="Path traversal detected"):
            SafeSanitizer.validate_safe_path("..\\..\\windows\\win.ini", base_dir)

        with pytest.raises(ValueError, match="Path traversal detected"):
            SafeSanitizer.validate_safe_path("/etc/shadow", base_dir)

    def test_mcp_run_benchmark_path_traversal_rejected(self):
        result = bionemo_run_benchmark(complexes_path="../../etc/passwd")
        assert "error" in result
        assert "Path traversal detected" in result["error"]


class TestPdbIdStrictValidation:
    """Verifies CWE-78 / Injection defense on PDB ID inputs."""

    def test_valid_pdb_ids_accepted(self):
        for pdb in ("7RPZ", "8AZV", "4MNE", "1UBQ", "2ITZ", "3PP0"):
            assert SafeSanitizer.validate_pdb_id(pdb) == pdb

    def test_malicious_pdb_ids_rejected(self):
        malicious_inputs = [
            "7RPZ; rm -rf /",
            "7RPZ\x00payload",
            "7RPZ\nls",
            "0ABC",          # Starts with zero
            "ABCD",          # Starts with letter
            "12",            # Too short
            "12345",         # Too long
            "../../etc",     # Traversal string
            "' OR '1'='1",   # SQL injection token
            "<script>",      # XSS token
        ]
        for bad_id in malicious_inputs:
            with pytest.raises(ValueError, match="PDB ID"):
                SafeSanitizer.validate_pdb_id(bad_id)

    def test_mcp_fetch_rcsb_pdb_rejects_malicious_id(self):
        res = bionemo_fetch_rcsb_pdb("7RPZ; rm -rf /")
        assert res["valid"] is False
        assert "Invalid PDB ID format" in res["error"]

    def test_api_target_pdb_endpoint_rejects_malicious_id(self, client):
        # Command injection pattern
        res = client.get("/api/target/pdb/7RPZ; rm -rf /")
        assert res.status_code == 400

        # Non-digit start
        res2 = client.get("/api/target/pdb/ABCD")
        assert res2.status_code == 400

        # Traversal sequence
        res3 = client.get("/api/target/pdb/....//etc/passwd")
        assert res3.status_code in (400, 403, 404)

        # Valid cached PDB
        res_ok = client.get("/api/target/pdb/8AZV")
        assert res_ok.status_code == 200
        assert "ATOM" in res_ok.text


class TestInputLengthAndControlCharBoundaries:
    """Verifies sequence and SMILES length boundaries and control character rejection."""

    def test_protein_sequence_rejects_null_and_control_chars(self):
        with pytest.raises(ValueError, match="illegal control characters or null bytes"):
            NimBioClient.validate_protein_sequence("MTEY\x00KLVVV")

        with pytest.raises(ValueError, match="illegal control characters or null bytes"):
            NimBioClient.validate_protein_sequence("MTEY\x07KLVVV")

    def test_protein_sequence_rejects_oversized_input(self):
        oversized = "M" * 10001
        with pytest.raises(ValueError, match="exceeds maximum permitted length"):
            NimBioClient.validate_protein_sequence(oversized)

    def test_smiles_rejects_null_and_control_chars(self):
        res = BenchmarkPipeline.sanitize_ligand_smiles("CC\x00(=O)Nc1ccc(O)cc1")
        assert res.is_valid is False
        assert "illegal control characters or null bytes" in (res.error_message or "")

    def test_smiles_rejects_oversized_input(self):
        oversized_smiles = "C" * 2001
        res = BenchmarkPipeline.sanitize_ligand_smiles(oversized_smiles)
        assert res.is_valid is False
        assert "exceeds maximum allowed limit" in (res.error_message or "")


class TestCSVFormulaInjectionAndXSSSanitization:
    """Verifies CWE-1236 (CSV Formula Injection) and DOM XSS neutralization in CSV outputs."""

    def test_sanitize_csv_formula_injection(self):
        # Cells beginning with formula triggers are prepended with a single quote
        assert SafeSanitizer.sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
        assert SafeSanitizer.sanitize_csv_cell("+1+1") == "'+1+1"
        assert SafeSanitizer.sanitize_csv_cell("-10.82") == "'-10.82"
        assert SafeSanitizer.sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
        assert SafeSanitizer.sanitize_csv_cell("\tDANGEROUS") == "'\tDANGEROUS"

    def test_sanitize_csv_html_tags(self):
        assert SafeSanitizer.sanitize_csv_cell("<script>alert('XSS')</script>") == "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        assert SafeSanitizer.sanitize_csv_cell('"><img src=x onerror=alert(1)>') == '&quot;&gt;&lt;img src=x onerror=alert(1)&gt;'

    def test_sanitize_csv_normal_values_untouched(self):
        assert SafeSanitizer.sanitize_csv_cell("NIM-LEAD-01-03") == "NIM-LEAD-01-03"
        assert SafeSanitizer.sanitize_csv_cell("CC(=O)N1CCNCC1") == "CC(=O)N1CCNCC1"


class TestSSRFOutboundHostAllowlist:
    """Verifies CWE-918 (Server-Side Request Forgery) defense and allowed host filtering."""

    def test_blocks_internal_and_disallowed_hosts(self):
        disallowed_urls = [
            "http://169.254.169.254/latest/meta-data/",
            "http://localhost:8000/internal",
            "http://127.0.0.1:22",
            "https://evil.com/exfiltrate",
            "http://files.rcsb.org/download/8AZV.pdb",  # Disallow unencrypted HTTP
            "https://user:pass@integrate.api.nvidia.com/v1",  # Embedded credentials
        ]
        for url in disallowed_urls:
            with pytest.raises(ValueError):
                SafeSanitizer.validate_outbound_url(url)

    def test_permits_allowlisted_https_hosts(self):
        allowed_urls = [
            "https://files.rcsb.org/download/8AZV.pdb",
            "https://data.rcsb.org/rest/v1/core/entry/8AZV",
            "https://integrate.api.nvidia.com/v1/biology/nvidia/esm2-650m",
            "https://health.api.nvidia.com/v1/biology/mit/diffdock",
        ]
        for url in allowed_urls:
            assert SafeSanitizer.validate_outbound_url(url) == url


class TestSecretsScrubberHygiene:
    """Verifies secret and token redaction from strings, logs, and exception messages."""

    def test_redacts_active_nvidia_api_key_env(self, monkeypatch):
        test_key = "nvapi-" + "my-secret-token-abcdef123456789"
        monkeypatch.setenv("NVIDIA_API_KEY", test_key)

        log_msg = f"Connection error while calling endpoint with key {test_key}: Timeout"
        scrubbed = SecretScrubber.scrub(log_msg)
        assert test_key not in scrubbed
        assert "[REDACTED_SECRET]" in scrubbed

    def test_redacts_bearer_and_patterns(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30"
        scrubbed = SecretScrubber.scrub(text)
        assert "eyJhbGci" not in scrubbed
        assert "[REDACTED_SECRET]" in scrubbed


class TestServerSecurityHeadersAndCORS:
    """Verifies HTTP security headers and CORS origin filtering on the local server."""

    def test_security_headers_present(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"

    def test_cors_allows_verified_origins(self, client):
        # Verified production origin
        res = client.options(
            "/api/health",
            headers={
                "Origin": "https://jorwalzzz.github.io",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res.headers.get("access-control-allow-origin") == "https://jorwalzzz.github.io"

        # Localhost development origin
        res_local = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res_local.headers.get("access-control-allow-origin") == "http://localhost:8000"

    def test_payload_size_ceiling(self, client):
        oversized_data = b"x" * (128 * 1024 + 10)
        res = client.post(
            "/api/run",
            content=oversized_data,
            headers={"Content-Length": str(len(oversized_data))},
        )
        assert res.status_code == 413
