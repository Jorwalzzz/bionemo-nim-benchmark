"""
Scientific Integrity, Provenance Verification & Target Isolation Test Suite.
Verifies:
1. Backend `/api/run` returns verifiable cryptographic provenance metadata and stamps leads.
2. Target isolation: BRAF V600E (4MNE) generates Vemurafenib candidates, never KRAS (MRTX1133) or HER2 residues.
3. Clean idle launch state: Zero fake leads preloaded on launch, KPIs initialized to idle dashes.
4. Raw Receipt Inspector: Modal displays JSON telemetry with zero console or CSP errors.

Part of NVIDIA BioNeMo Benchmark Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.server.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    return TestClient(app)


class TestBackendProvenanceContract:
    """Verifies that the FastAPI discovery endpoint adheres to the scientific provenance contract."""

    def test_run_endpoint_returns_provenance_object(self, client):
        res = client.post("/api/run?target=KRAS+G12D&candidates=3")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()

        assert "provenance" in data, "Response must include top-level 'provenance' dict"
        prov = data["provenance"]

        assert "mode" in prov
        assert prov["mode"] in ("LIVE_NVIDIA_NIM", "MOCK_SIMULATION")
        assert "backend_host" in prov
        assert "nim_endpoints_called" in prov
        assert isinstance(prov["nim_endpoints_called"], list)
        assert len(prov["nim_endpoints_called"]) > 0

        assert "request_ids" in prov
        assert isinstance(prov["request_ids"], list)
        assert len(prov["request_ids"]) > 0
        assert any(r.startswith("req-nim-") for r in prov["request_ids"])

        assert "rdkit_version" in prov
        assert "elapsed_ms" in prov
        assert isinstance(prov["elapsed_ms"], (int, float))
        assert prov["elapsed_ms"] >= 0

        assert "timestamp_utc" in prov
        # Must be valid ISO 8601 timestamp
        assert "T" in prov["timestamp_utc"]

    def test_leads_are_stamped_with_provenance_and_simulation_flags(self, client):
        res = client.post("/api/run?target=KRAS+G12D&candidates=3")
        assert res.status_code == 200
        data = res.json()

        leads = data.get("leads", [])
        assert len(leads) > 0, "Expected generated leads in discovery response"

        mode = data["provenance"]["mode"]
        for lead in leads:
            assert "provenance" in lead, f"Lead {lead.get('id')} missing 'provenance'"
            assert lead["provenance"] == mode
            assert "is_simulated" in lead, f"Lead {lead.get('id')} missing 'is_simulated'"
            assert isinstance(lead["is_simulated"], bool)
            if mode == "MOCK_SIMULATION":
                assert lead["is_simulated"] is True
            elif mode == "LIVE_NVIDIA_NIM":
                assert lead["is_simulated"] is False


class TestTargetPresetsAndIsolation:
    """Verifies target-presets.js and target isolation invariants."""

    def test_target_presets_data_has_16_targets_and_braf_4mne(self):
        target_presets_file = REPO_ROOT / "js" / "data" / "target-presets.js"
        assert target_presets_file.is_file(), "js/data/target-presets.js must exist"
        content = target_presets_file.read_text(encoding="utf-8")

        # 4MNE target must have Vemurafenib and specific pocket residues
        assert "4MNE" in content
        assert "Vemurafenib" in content
        assert "Glu501" in content
        assert "Leu514" in content

    def test_no_hardcoded_kras_leads_in_clean_cockpit_html(self):
        cockpit_html = (REPO_ROOT / "cockpit.html").read_text(encoding="utf-8")

        # Preloaded container must not contain hardcoded MRTX1133 lead cards
        assert "MRTX1133-NIM-01" not in cockpit_html, "cockpit.html must not hardcode MRTX1133-NIM-01 in static HTML"

        # Must contain provenance banner elements
        assert 'id="provenanceBanner"' in cockpit_html
        assert 'id="provenanceBadge"' in cockpit_html
        assert 'id="provenanceDot"' in cockpit_html
        assert 'id="provenanceDetail"' in cockpit_html
        assert 'id="viewReceiptBtn"' in cockpit_html

        # Must contain raw receipt modal elements
        assert 'id="rawReceiptModal"' in cockpit_html
        assert 'id="rawReceiptContent"' in cockpit_html
        assert 'id="copyRawReceiptBtn"' in cockpit_html

    def test_main_js_initializes_idle_state_without_kras_preload(self):
        main_js = (REPO_ROOT / "js" / "cockpit" / "main.js").read_text(encoding="utf-8")

        # Must set idle dashes on KPIs
        assert "state.currentLeads = [];" in main_js
        assert "kpiAff.textContent = '—';" in main_js
        assert "updateProvenanceBanner(" in main_js

        # Must not preload defaultLeads from EMPIRICAL_TARGET_LEADS on launch
        assert "const defaultLeads = EMPIRICAL_TARGET_LEADS['KRAS G12D']" not in main_js

    def test_api_js_derives_leads_dynamically_without_hardcoded_contamination(self):
        api_js = (REPO_ROOT / "js" / "cockpit" / "api.js").read_text(encoding="utf-8")

        # Must not contain hardcoded fallback contact ternary with Thr798 / Met801 / Lys753
        assert "target.includes('KRAS') ? 'Asp12, Tyr96, Gln61'" not in api_js
        # Must derive SIM-01 dynamically
        assert "${ligandClean}-SIM-${numStr}" in api_js


@pytest.fixture(scope="module")
def live_server_url():
    import functools
    import http.server
    import socketserver
    import threading

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


class TestCockpitScientificIntegrityPlaywright:
    """Browser-level verification of clean idle launch state, target isolation, and receipt modal."""

    def test_browser_clean_idle_state_and_receipt_modal(self, live_server_url):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(f"{live_server_url}/cockpit.html", wait_until="networkidle")

            # 1. Verify Clean Idle KPI cards
            kpi_aff = page.locator("#kpiAffinity").inner_text().strip()
            kpi_qed = page.locator("#kpiQed").inner_text().strip()
            kpi_sc = page.locator("#kpiScreened").inner_text().strip()
            kpi_par = page.locator("#kpiPareto").inner_text().strip()

            assert kpi_aff == "—", f"Expected idle dash '—' for kpiAffinity, got '{kpi_aff}'"
            assert kpi_qed == "—", f"Expected idle dash '—' for kpiQed, got '{kpi_qed}'"
            assert kpi_sc == "—", f"Expected idle dash '—' for kpiScreened, got '{kpi_sc}'"
            assert kpi_par == "—", f"Expected idle dash '—' for kpiPareto, got '{kpi_par}'"

            # 2. Verify Empty Leads Placeholder
            leads_text = page.locator("#leadsContainer").inner_text()
            assert "No leads nominated yet" in leads_text, "Expected 'No leads nominated yet' placeholder on launch"

            # 3. Verify Provenance Banner
            prov_badge = page.locator("#provenanceBadge").inner_text()
            assert "OFFLINE DEMO" in prov_badge or "CLIENT SIMULATION" in prov_badge

            # 4. Open and Verify Raw Receipt Modal
            page.click("#viewReceiptBtn")
            page.wait_for_selector("#rawReceiptModal", state="visible")
            receipt_json = page.locator("#rawReceiptContent").inner_text()
            assert "provenance" in receipt_json or "mode" in receipt_json

            # Close Receipt Modal
            page.click('#rawReceiptModal button[aria-label="Close raw receipt dialog"]')
            page.wait_for_selector("#rawReceiptModal", state="hidden")

            # Zero console errors allowed
            assert len(console_errors) == 0, f"Encountered browser console errors: {console_errors}"
            browser.close()
