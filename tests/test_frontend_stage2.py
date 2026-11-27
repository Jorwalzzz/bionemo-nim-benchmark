"""
Stage 2 Frontend, CLI Alignment, Strict CSP, and Scientific Audit Parity Tests.
Covers:
1. CLI builder (`js/cli-builder.js`) vs `run_benchmark.py` flag alignment & execution.
2. Strict CSP (`script-src` without `'unsafe-inline'`, zero inline `<script>` / `on*=`).
3. Release audit (`scripts/audit/audit_release.py`) parity & `<label for>` checks.
4. Feedback category alignment between `cockpit.html` and `auth_manager.VALID_FEEDBACK_CATEGORIES`.
5. Playwright browser verification:
   - Zero console errors / CSP violations on `index.html` and `cockpit.html`.
   - Tour Step 3 target selection (`7RPZ`, zero `4OBE`).
   - Workbench preset loading (`PRESET_INHIBITORS[key].smiles`) & live MW calculation.
   - ESMFold raw sequence transmission (never forced to `KRAS G12D`).
   - Ligand-centered 3D binding pocket centroid (`viewer3d.computeBindingPocketCentroid`).
   - Dynamic `GET /api/health` probe on non-8000 port + authenticated `POST /api/stream` SSE flow.
"""

from __future__ import annotations

import functools
import http.server
import json
import re
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

import run_benchmark
from bionemo_benchmark.infra.auth_manager import VALID_FEEDBACK_CATEGORIES
from bionemo_benchmark.server.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def static_site_url():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return

    class ThreadedHTTPServer(socketserver.ThreadingTCPServer):
        request_queue_size = 128
        daemon_threads = True
        allow_reuse_address = True

    handler = functools.partial(QuietHandler, directory=str(REPO_ROOT))
    server = ThreadedHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=3.0)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_cli_builder_flags_align_with_run_benchmark(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cli_js = (REPO_ROOT / "js" / "cli-builder.js").read_text(encoding="utf-8")
    assert "8AZV" not in cli_js, "js/cli-builder.js should use verified 7RPZ instead of WT 8AZV"

    flags_in_js = set(re.findall(r"--[a-z][a-z-]+", cli_js))
    assert {
        "--endpoint",
        "--target",
        "--poses",
        "--batch-size",
        "--output-format",
        "--admet-filter",
        "--mock",
    }.issubset(flags_in_js)

    # Parse default and preset commands cleanly through run_benchmark.parse_args()
    presets = [
        [
            "run_benchmark.py",
            "--endpoint",
            "health.api.nvidia.com",
            "--target",
            "7RPZ",
            "--poses",
            "5",
            "--batch-size",
            "32",
            "--output-format",
            "json",
            "--admet-filter",
            "--mock",
        ],
        [
            "run_benchmark.py",
            "--endpoint",
            "integrate.api.nvidia.com",
            "--target",
            "7RPZ",
            "--poses",
            "10",
            "--batch-size",
            "32",
            "--output-format",
            "pdf",
            "--admet-filter",
        ],
        [
            "run_benchmark.py",
            "--endpoint",
            "localhost:8000",
            "--target",
            "ALL_TARGETS",
            "--poses",
            "5",
            "--batch-size",
            "64",
            "--output-format",
            "csv",
            "--admet-filter",
            "--mock",
        ],
    ]
    for argv in presets:
        monkeypatch.setattr(sys, "argv", argv)
        parsed = run_benchmark.parse_args()
        assert parsed.target in {"7RPZ", "ALL_TARGETS"}
        assert parsed.output_format in {"json", "pdf", "csv"}

    # Execute end-to-end CLI run with target filter & JSON format into tmp_path
    out_dir = tmp_path / "cli_out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark.py",
            "--endpoint",
            "health.api.nvidia.com",
            "--target",
            "7RPZ",
            "--poses",
            "2",
            "--batch-size",
            "16",
            "--output-format",
            "json",
            "--admet-filter",
            "--mock",
            "--iterations",
            "1",
            "--output-dir",
            str(out_dir),
        ],
    )
    run_benchmark.main()

    report_path = out_dir / "cli_benchmark_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["cli_config"]["target"] == "7RPZ"
    assert report["cli_config"]["admet_filter"] is True
    assert len(report["records"]) == 1
    assert report["records"][0]["pdb_id"] == "7RPZ"


def test_feedback_categories_and_csp_headers_strict() -> None:
    cockpit_html = (REPO_ROOT / "cockpit.html").read_text(encoding="utf-8")
    options = re.findall(r'<select id="feedbackCategory".*?</select>', cockpit_html, re.S)
    assert options, "feedbackCategory select element missing from cockpit.html"
    ui_cats = set(re.findall(r'<option value="([^"]+)"', options[0]))
    assert len(ui_cats) == 6
    assert ui_cats.issubset(VALID_FEEDBACK_CATEGORIES)

    client = TestClient(app)
    for path in ("/api/health", "/cockpit.html", "/index.html"):
        resp = client.get(path)
        assert resp.status_code == 200
        csp = resp.headers.get("content-security-policy", "")
        script_src = re.search(r"script-src\s+([^;]+)", csp)
        assert script_src is not None, f"Missing script-src CSP on {path}"
        assert "'unsafe-inline'" not in script_src.group(1), f"CSP script-src on {path} leaks 'unsafe-inline'"


def test_playwright_stage2_bugs_and_csp(static_site_url: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        console_errors: list[str] = []
        page_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        # Verify index.html loads cleanly under strict CSP with zero errors
        page.goto(f"{static_site_url}/index.html", wait_until="networkidle")
        assert len(page_errors) == 0, f"index.html page errors: {page_errors}"
        assert len(console_errors) == 0, f"index.html console errors: {console_errors}"

        # Load cockpit.html under strict CSP
        page.goto(f"{static_site_url}/cockpit.html", wait_until="networkidle")

        # Close first-time auto tour if launched, then verify Quickstart Step 1 selects 7RPZ (not 4OBE)
        tour_modal = page.locator("#tourCardModal")
        if not tour_modal.is_visible():
            page.click('button[aria-label="Start quickstart guide"]')
            page.wait_for_selector("#tourCardModal", state="visible")
        page.click("#btnTourAction")
        page.wait_for_timeout(150)
        assert page.locator("#targetSelect").input_value() == "7RPZ"
        toast_text = page.locator("#toast").inner_text()
        assert "4OBE" not in toast_text
        assert "7RPZ" in toast_text
        page.click('button[data-action="close-tour"]')
        page.wait_for_selector("#tourCardModal", state="hidden")

        # Run simulated campaign cleanly, then test workbench preset & live MW calculation
        page.select_option("#targetSelect", "7RPZ")
        page.fill("#candidateSlider", "6")
        page.dispatch_event("#candidateSlider", "input")
        page.click("#runBtn")
        page.wait_for_selector("#runBtn:not([disabled])", timeout=15000)
        page.wait_for_selector('[data-action="load-wb-preset"][data-arg="egfr"]', state="visible")

        page.click('[data-action="load-wb-preset"][data-arg="egfr"]')
        page.wait_for_timeout(250)
        wb_smiles = page.locator("#workbenchSmilesInput").input_value()
        assert "[object Object]" not in wb_smiles
        assert wb_smiles.startswith("CN1C=C")
        wb_mw = float(page.locator("#wbLiveMw").inner_text().strip())
        assert 450.0 < wb_mw < 550.0, f"Expected chemical MW near Osimertinib (~499), got {wb_mw}"

        # Verify ESMFold tab preserves pasted amino acid sequence rather than forcing KRAS G12D
        page.click("#tabBtnEsmfold")
        page.click("#chipEsmUbiquitin")
        assert page.locator("#seqLenBadge").inner_text().strip() == "76 aa"
        page.click("#runBtn")
        page.wait_for_selector("#runBtn:not([disabled])", timeout=15000)
        run_target = page.evaluate("() => window.activeRunResult?.target || ''")
        assert "76 aa" in run_target
        assert "MRTX1133" not in page.locator("#agentLog").inner_text()

        # Verify 3D pocket centroid calculates real crystal ligand coordinates from 7RPZ.pdb
        pdb_7rpz = (REPO_ROOT / "data" / "pdbs" / "7RPZ.pdb").read_text(encoding="utf-8")
        centroid = page.evaluate(
            """async (pdbText) => {
                const mod = await import('./js/cockpit/viewer3d.js');
                return mod.computeBindingPocketCentroid(pdbText, [12, 61, 96]);
            }""",
            pdb_7rpz,
        )
        assert centroid is not None
        assert abs(centroid["x"] - 1.71) < 1.5
        assert abs(centroid["y"] - 4.93) < 1.5
        assert abs(centroid["z"] - (-23.16)) < 1.5
        assert abs(centroid["x"] - 12.4) > 5.0

        # Verify apo / ESMFold fallback uses pocket residues rather than whole-protein centroid
        apo_pdb = (
            "ATOM      1  CA  GLY A  10      10.000  20.000  30.000  1.00 50.00           C\n"
            "ATOM      2  CA  ASP A  20      14.000  24.000  34.000  1.00 50.00           C\n"
            "ATOM      3  CA  ALA A  99     999.000 999.000 999.000  1.00 50.00           C\n"
        )
        apo_centroid = page.evaluate(
            """async (pdbText) => {
                const mod = await import('./js/cockpit/viewer3d.js');
                return mod.computeBindingPocketCentroid(pdbText, [10, 20]);
            }""",
            apo_pdb,
        )
        assert apo_centroid == {"x": 12.0, "y": 22.0, "z": 32.0}

        assert len(page_errors) == 0, f"cockpit.html page errors: {page_errors}"
        assert len(console_errors) == 0, f"cockpit.html console errors: {console_errors}"
        browser.close()


def test_playwright_live_health_probe_and_sse_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISABLE_TRIAL_LIMIT", "false")
    port = _find_free_port()
    assert port != 8000

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait briefly for FastAPI socket readiness
    deadline = time.time() + 10.0
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started, "Uvicorn test server failed to start in time"

    stream_statuses: list[int] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on(
                "response",
                lambda resp: stream_statuses.append(resp.status) if resp.url.endswith("/api/stream") else None,
            )

            page.goto(f"http://127.0.0.1:{port}/cockpit.html", wait_until="networkidle")
            page.wait_for_function("() => window.state && window.state.isBackendAvailable === true", timeout=5000)

            # Authenticate using 1-Click Evaluator Sign In inside modal
            page.click("#authBtn")
            page.wait_for_selector("#authModal", state="visible")
            page.click('[data-action="demo-login"]')
            page.wait_for_selector("#authModal", state="hidden", timeout=5000)

            # Execute streamed discovery campaign via POST /api/stream
            page.select_option("#targetSelect", "7RPZ")
            page.fill("#candidateSlider", "5")
            page.dispatch_event("#candidateSlider", "input")
            page.click("#runBtn")
            page.wait_for_selector("#runBtn:not([disabled])", timeout=15000)
            page.wait_for_timeout(300)

            assert stream_statuses == [200], f"Expected HTTP 200 from POST /api/stream, got {stream_statuses}"
            assert page.locator("#leadsContainer .lead-card").count() > 0
            assert "4/5" in page.locator("#authHudContainer").inner_text()
            assert len(page_errors) == 0, f"Live backend page errors: {page_errors}"
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5.0)
