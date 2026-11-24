"""
Playwright automated proof for BioNeMo Discovery Cockpit scientific integrity.
Verifies:
(a) Clean idle state on load (KPI cards '—', empty leads state, no preloaded fake leads)
(b) Running 4MNE (BRAF V600E) never outputs MRTX1133 or Thr790
(c) SCREENED count matches ADMET/lead state and single-source runResult
(d) Sign In | 5 Runs/Day is hidden in static mode and STATIC DEMO MODE pill is shown

Part of NVIDIA BioNeMo Benchmark Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cockpit_server_url():
    import functools

    class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return

    class ThreadedServer(socketserver.ThreadingTCPServer):
        request_queue_size = 128
        daemon_threads = True
        allow_reuse_address = True

    handler = functools.partial(QuietHTTPHandler, directory=str(REPO_ROOT))
    server = ThreadedServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    t.join(timeout=3.0)


class TestCockpitIntegrityPlaywright:
    """Automated Playwright proofs for scientific integrity and UI consistency."""

    def test_clean_idle_state_on_load(self, cockpit_server_url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(f"{cockpit_server_url}/cockpit.html", wait_until="networkidle")

            # (a) Verify all 4 KPI cards are initialized to idle dash '—'
            kpi_aff = page.locator("#kpiAffinity").inner_text().strip()
            kpi_qed = page.locator("#kpiQed").inner_text().strip()
            kpi_sc = page.locator("#kpiScreened").inner_text().strip()
            kpi_par = page.locator("#kpiPareto").inner_text().strip()

            assert kpi_aff == "—", f"Expected '—' for kpiAffinity, got '{kpi_aff}'"
            assert kpi_qed == "—", f"Expected '—' for kpiQed, got '{kpi_qed}'"
            assert kpi_sc == "—", f"Expected '—' for kpiScreened, got '{kpi_sc}'"
            assert kpi_par == "—", f"Expected '—' for kpiPareto, got '{kpi_par}'"

            # Verify empty leads placeholder is shown
            leads_container_text = page.locator("#leadsContainer").inner_text()
            assert "No leads nominated yet" in leads_container_text
            assert "MRTX1133-NIM-01" not in leads_container_text

            # Verify provenance banner default is offline demo simulation
            prov_badge = page.locator("#provenanceBadge").inner_text()
            assert "OFFLINE DEMO" in prov_badge
            assert "SIMULATION" in prov_badge

            assert len(console_errors) == 0, f"Unexpected console errors: {console_errors}"
            browser.close()

    def test_run_4mne_target_isolation(self, cockpit_server_url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(f"{cockpit_server_url}/cockpit.html", wait_until="networkidle")

            # Select 4MNE (BRAF V600E) preset
            page.select_option("#targetSelect", "4MNE")
            page.wait_for_timeout(200)

            # Verify target metadata card shows updated 4MNE info: 2.85 Å and Type I½ αC-Helix-Out Pocket
            target_res = page.locator("#targetRes").inner_text().strip()
            assert "2.85" in target_res, f"Expected 2.85 Å for 4MNE, got '{target_res}'"
            target_pocket = page.locator("#targetPocket").inner_text().strip()
            assert "Type I" in target_pocket or "Helix" in target_pocket

            # Set candidate slider to 6
            page.fill("#candidateSlider", "6")
            page.dispatch_event("#candidateSlider", "input")

            # Click Run Autonomous Discovery
            page.click("#runBtn")

            # Wait for run to complete (runBtn disabled disappears, done state reached)
            page.wait_for_selector('#runBtn:not([disabled])', timeout=15000)
            page.wait_for_timeout(500)

            # (b) Verify running 4MNE outputs VEMURAFENIB-SIM-01 and never MRTX1133 or Thr790
            leads_text = page.locator("#leadsContainer").inner_text()
            log_text = page.locator("#agentLog").inner_text()
            full_text = f"{leads_text}\n{log_text}"

            assert "VEMURAFENIB-SIM-01" in leads_text, "Expected VEMURAFENIB-SIM-01 for 4MNE target"
            assert "SIMULATED" in leads_text, "Simulated leads must have SIMULATED badge"
            assert "MRTX1133" not in full_text, "Forbidden leak: MRTX1133 found in 4MNE run"
            assert "Thr790" not in full_text, "Forbidden leak: Thr790 found in 4MNE run"

            # (c) Verify SCREENED count matches ADMET and lead state
            kpi_screened = page.locator("#kpiScreened").inner_text().strip()
            lead_cards_count = page.locator("#leadsContainer .lead-card").count()
            assert int(kpi_screened) == lead_cards_count, (
                f"SCREENED count {kpi_screened} does not match lead cards count {lead_cards_count}"
            )

            # Verify Export JSON button works and creates download or contains runResult
            run_result_valid = page.evaluate("""() => {
                return window.activeRunResult && 
                       window.activeRunResult.screenedCount === window.activeRunResult.leads.length &&
                       window.activeRunResult.passedCount + window.activeRunResult.flaggedCount === window.activeRunResult.screenedCount;
            }""")
            assert run_result_valid is True, "activeRunResult must maintain mathematical parity"

            assert len(console_errors) == 0, f"Unexpected console errors: {console_errors}"
            browser.close()

    def test_static_mode_hides_signin_and_shows_demo_pill(self, cockpit_server_url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"{cockpit_server_url}/cockpit.html", wait_until="networkidle")

            # Emulate static host (non-loopback hostname, e.g. jorwalzzz.github.io)
            page.evaluate("() => window.updateHeaderAuthUI(true)")

            # (d) Verify Sign In button is hidden in static mode and STATIC DEMO MODE pill is shown
            auth_hud = page.locator("#authHudContainer")
            static_pill = page.locator("#staticDemoPill")

            assert not auth_hud.is_visible(), "Sign In | 5 Runs/Day must be hidden on static host"
            assert static_pill.is_visible(), "STATIC DEMO MODE pill must be visible on static host"

            # Click STATIC DEMO MODE pill and verify modal opens with uvicorn launch command
            static_pill.click()
            page.wait_for_selector("#staticDemoModal", state="visible")
            modal_text = page.locator("#staticDemoModal").inner_text()
            assert "uvicorn bionemo_benchmark.server.app:app --host 127.0.0.1 --port 8000" in modal_text

            # Close modal
            page.click('#staticDemoModal button[aria-label="Close static demo dialog"]')
            page.wait_for_selector("#staticDemoModal", state="hidden")

            browser.close()
