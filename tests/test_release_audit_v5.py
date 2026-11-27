"""
Regression and parity verification tests for Phase 4 frontend/cockpit release audit hardening.
Part of NVIDIA BioNeMo Agentic Scientist Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from bionemo_benchmark.server.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "audit"))
import audit_release  # noqa: E402


def test_speedup_benchmark_reads_summary_json_gpu_latencies() -> None:
    """GET /api/benchmark/speedup must reflect H100 latencies from results/benchmark_summary.json."""
    summary_data = json.loads((REPO_ROOT / "results" / "benchmark_summary.json").read_text(encoding="utf-8"))
    expected_ms: dict[str, float] = {}
    for row in summary_data["benchmarks"]:
        svc = str(row["nim_service"])
        if "ESM-2" in svc:
            expected_ms["ESM-2"] = round(float(row["gpu_latency_s"]) * 1000.0, 1)
        elif "MolMIM" in svc:
            expected_ms["MolMIM"] = round(float(row["gpu_latency_s"]) * 1000.0, 1)
        elif "DiffDock" in svc:
            expected_ms["DiffDock"] = round(float(row["gpu_latency_s"]) * 1000.0, 1)

    client = TestClient(app)
    resp = client.get("/api/benchmark/speedup")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["basis"] == "Illustrative"
    tasks_by_name = {t["module"]: t for t in payload["tasks"]}
    assert any(t["h100_latency_ms"] == expected_ms["ESM-2"] for k, t in tasks_by_name.items() if "ESM-2" in k)
    assert any(t["h100_latency_ms"] == expected_ms["MolMIM"] for k, t in tasks_by_name.items() if "MolMIM" in k)
    assert any(t["h100_latency_ms"] == expected_ms["DiffDock"] for k, t in tasks_by_name.items() if "DiffDock" in k)


def test_js_csv_formula_neutralization_and_quoting() -> None:
    """Verify js/shared/dom-utils.js toCsvCell neutralizes spreadsheet formulas and quotes commas."""
    node_script = r"""
import { toCsvCell } from './js/shared/dom-utils.js';
import assert from 'node:assert/strict';

assert.equal(toCsvCell('=CMD("calc")'), '"\'=CMD(""calc"")"');
assert.equal(toCsvCell('+SUM(A1:A2)'), "'+SUM(A1:A2)");
assert.equal(toCsvCell('-1+1'), "'-1+1");
assert.equal(toCsvCell('@SUM(1,2)'), '"\'@SUM(1,2)"');
assert.equal(toCsvCell('\t=2+2'), "'\t=2+2");
assert.equal(toCsvCell('KRAS, G12D'), '"KRAS, G12D"');
assert.equal(toCsvCell('normal_lead'), 'normal_lead');
console.log('CSV_PASS');
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Node CSV check failed: {proc.stderr}"
    assert "CSV_PASS" in proc.stdout


def test_release_audit_script_passes_cleanly() -> None:
    """audit_release.py must report 0 errors and 0 warnings across the repository."""
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit" / "audit_release.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"audit_release.py failed:\n{proc.stdout}\n{proc.stderr}"
    assert "0 ERROR(S), 0 WARNING(S)" in proc.stdout


def test_release_audit_rejects_accessibility_and_token_regressions(tmp_path: Path) -> None:
    """Negative fixture audit: detect missing button type, role=button, and undefined CSS vars."""
    (tmp_path / "results").mkdir(exist_ok=True)
    css_dir = tmp_path / "css"
    css_dir.mkdir(exist_ok=True)
    (css_dir / "tokens.css").write_text(":root { --color-canvas: #05070a; }\n", encoding="utf-8")
    (css_dir / "bad.css").write_text(".box { color: var(--undefined-token-xyz); }\n", encoding="utf-8")

    html_file = tmp_path / "bad.html"
    html_file.write_text(
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<link rel="stylesheet" href="./css/tokens.css">'
        '<link rel="stylesheet" href="./css/bad.css">'
        "</head><body>"
        '<button id="missingType">Click</button>'
        '<div role="button">Fake</div>'
        "</body></html>",
        encoding="utf-8",
    )

    state = audit_release.validate_html_file(html_file, tmp_path)
    msgs = [i.message for i in state.issues]
    assert any("missing explicit `type` attribute" in m for m in msgs)
    assert any('Non-semantic `<div role="button">`' in m for m in msgs)
    assert any("--undefined-token-xyz" in m for m in msgs)
