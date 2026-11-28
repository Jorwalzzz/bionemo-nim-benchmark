"""Sprint 1 verification tests: version parity, CSV alignment, and run_id-isolated dossier."""

from __future__ import annotations

from fastapi.testclient import TestClient

from bionemo_benchmark import __version__
from bionemo_benchmark.infra.security_sentinel import SafeSanitizer
from bionemo_benchmark.server.app import app


def test_package_version_is_2_3_0() -> None:
    assert __version__ == "2.3.0"


def test_csv_sanitizer_preserves_numeric_and_neutralizes_formulas() -> None:
    assert SafeSanitizer.sanitize_csv_cell(-9.50) == "-9.5"
    assert SafeSanitizer.sanitize_csv_cell("-0.42") == "-0.42"
    assert SafeSanitizer.sanitize_csv_cell("=SUM(A1)") == "'=SUM(A1)"
    assert SafeSanitizer.sanitize_csv_cell(" -1+1") == "' -1+1"
    assert SafeSanitizer.sanitize_csv_cell("@CMD") == "'@CMD"
    assert SafeSanitizer.sanitize_csv_cell("foo,bar") == "foo,bar"
    assert SafeSanitizer.sanitize_csv_cell(None) == ""


def test_dossier_run_id_isolation_and_static_fallback(monkeypatch) -> None:
    monkeypatch.setenv("DISABLE_TRIAL_LIMIT", "true")
    client = TestClient(app)

    # 1. Omitted run_id -> static archive
    static_resp = client.get("/api/dossier")
    assert static_resp.status_code == 200
    assert static_resp.headers.get("x-dossier-source") == "static-archive"

    # 2. Unknown run_id -> 404 (no cross-session leak)
    missing_resp = client.get("/api/dossier?run_id=run-nonexistent")
    assert missing_resp.status_code == 404

    # 3. Live run populates LRU cache and returns X-Dossier-Source: live-run
    run_resp = client.post(
        "/api/run?target=KRAS%20G12D&candidates=5",
        headers={"X-BioNeMo-CSRF": "1"},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run_id"]
    live_resp = client.get(f"/api/dossier?run_id={run_id}")
    assert live_resp.status_code == 200
    assert live_resp.headers.get("x-dossier-source") == "live-run"
    assert run_id in live_resp.text
