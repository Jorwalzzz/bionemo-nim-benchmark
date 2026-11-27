"""Behavioral Playwright regression tests for Cockpit post-run upgrades."""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def _start_static_server() -> tuple[ThreadingHTTPServer, int]:
    handler = partial(_QuietHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_cockpit_postrun_state_csv_pose_history_and_keyboard() -> None:
    server, port = _start_static_server()
    base_url = f"http://127.0.0.1:{port}/cockpit.html"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
            page = context.new_page()

            console_errors: list[str] = []
            http_404s: list[str] = []
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
            )
            page.on(
                "response",
                lambda resp: http_404s.append(resp.url) if resp.status == 404 else None,
            )

            page.goto(base_url, wait_until="networkidle")
            page.keyboard.press("Escape")

            # 1. Verify numeric-preserving CWE-1236 toCsvCell directly in browser module
            csv_results = page.evaluate(
                """async () => {
                    const { toCsvCell } = await import('./js/shared/dom-utils.js');
                    return {
                        negFloat: toCsvCell(-9.50),
                        negStr: toCsvCell('-0.42'),
                        formulaEq: toCsvCell('=SUM(A1)'),
                        formulaLeadSpace: toCsvCell(' -1+1'),
                        quotedComma: toCsvCell('a,"b",c')
                    };
                }"""
            )
            assert csv_results["negFloat"] == "-9.5"
            assert csv_results["negStr"] == "-0.42"
            assert csv_results["formulaEq"] == "'=SUM(A1)"
            assert csv_results["formulaLeadSpace"] == "' -1+1"
            assert csv_results["quotedComma"] == '"a,""b"",c"'

            # 2. Seed 2 leads with 2 poses each, select lead #2, re-dock, verify ID-locked selection & Revert
            page.evaluate(
                """async () => {
                    const { renderLeads, selectLead, pushRunHistory, renderRunHistoryStrip } = await import('./js/cockpit/ui-controls.js');
                    const makeLead = (id, aff, qed) => ({
                        id,
                        smiles: 'CC(=O)Nc1ccc(O)cc1',
                        affinity: aff,
                        qed,
                        sascore: 2.3,
                        mw: 151.16,
                        verdict: 'PASS',
                        pareto: true,
                        provenance: 'SIMULATED',
                        pose_sdf: 'LEAD_SDF_' + id + '\\nM  END\\n',
                        poses: [
                            { rank: 1, predicted_affinity_kcal_mol: aff, provenance: 'SIMULATED', interaction_contacts: [{ type: 'H-Bond', residue: 'ASP12', distance_a: 2.1 }], pose_validation: { passes_all: true, bond_geometry_pass: true, receptor_clash_pass: true, receptor_clash_count: 0, planarity_pass: true, strain_energy_kcal_mol: 1.2 } },
                            { rank: 2, predicted_affinity_kcal_mol: aff + 0.5, provenance: 'SIMULATED', interaction_contacts: [{ type: 'Hydrophobic', residue: 'TYR96', distance_a: 3.4 }], pose_validation: { passes_all: false, bond_geometry_pass: true, receptor_clash_pass: false, receptor_clash_count: 2, planarity_pass: true, strain_energy_kcal_mol: 4.8 } }
                        ],
                        interaction_contacts: [{ type: 'H-Bond', residue: 'ASP12', distance_a: 2.1 }],
                        pose_validation: { passes_all: true, bond_geometry_pass: true, receptor_clash_pass: true, receptor_clash_count: 0, planarity_pass: true, strain_energy_kcal_mol: 1.2 }
                    });
                    window.isOwner = true;
                    window.state.runId = 'run-1';
                    window.state.currentLeads = [makeLead('LEAD-A', -9.2, 0.75), makeLead('LEAD-B', -8.6, 0.81)];
                    window.state.activeRunResult = { runId: 'run-1', target: 'KRAS G12D', pdbId: '7RPZ', provenance: 'SIMULATED', leads: window.state.currentLeads, topLead: window.state.currentLeads[0], screenedCount: 2, paretoCount: 2 };
                    pushRunHistory(window.state.activeRunResult);
                    renderRunHistoryStrip();
                    renderLeads();
                    selectLead(1);
                }"""
            )
            assert page.evaluate("window.state.selectedLeadId") == "LEAD-B"

            # Re-dock lead #2 and verify selection stays on LEAD-B, delta strip appears, and JSON has no _baseline
            page.locator('#workbenchSmilesInput').fill('Fc1ccc(NC(=O)C)cc1')
            page.locator('[data-action="trigger-redock"]').click()
            page.wait_for_selector('[data-action="revert-lead"]')
            assert page.evaluate("window.state.selectedLeadId") == "LEAD-B"
            serialized = page.evaluate("JSON.stringify(window.state.currentLeads)")
            assert "_baseline" not in serialized

            # Revert to original
            page.locator('[data-action="revert-lead"]').click()
            assert page.evaluate("window.state.currentSelectedLead.affinity") == -8.6
            assert page.locator('[data-action="revert-lead"]').count() == 0

            # 3. In-place pose switching (Pose 1 -> Pose 2) preserves #dossierPanel identity
            page.evaluate("window.__dossierNode = document.getElementById('dossierPanel').firstElementChild;")
            page.locator('[data-action="select-docked-pose"][data-arg="1"]').click()
            same_node = page.evaluate("window.__dossierNode === document.getElementById('dossierPanel').firstElementChild")
            assert same_node is True
            assert "TYR96" in page.locator('#contactsContainer').inner_text()
            assert "REVIEW" in page.locator('#posePlausibilityContainer').inner_text()

            # 4. Safe keyboard triage: Ctrl+1 and open <dialog> must NOT switch pose; plain '1' switches back to Pose 1
            page.keyboard.press("Control+1")
            assert page.evaluate("window.state.selectedPoseIndex") == 1
            page.evaluate("document.getElementById('authModal')?.showModal()")
            page.keyboard.press("1")
            assert page.evaluate("window.state.selectedPoseIndex") == 1
            page.keyboard.press("Escape")
            page.keyboard.press("1")
            assert page.evaluate("window.state.selectedPoseIndex") == 0

            # ArrowDown inside #leadsContainer advances focus/selection
            page.locator('#leadsContainer .lead-card').first.focus()
            page.keyboard.press("ArrowDown")
            assert page.evaluate("window.state.selectedLeadId") == "LEAD-B"

            # 5. Run history (3 runs) + restore Run 1 + adoptEvolvedScaffold reactive update
            page.evaluate(
                """async () => {
                    const { pushRunHistory, renderRunHistoryStrip } = await import('./js/cockpit/ui-controls.js');
                    const { adoptEvolvedScaffold } = await import('./js/cockpit/exports.js');
                    for (const [id, pdb, aff] of [['run-2', '4MNE', -9.8], ['run-3', '7L0D', -8.9]]) {
                        const lead = { id: 'L-' + pdb, smiles: 'CCO', affinity: aff, qed: 0.7, sascore: 2.0, mw: 46.07, verdict: 'PASS', pareto: true, provenance: 'SIMULATED' };
                        window.state.runId = id;
                        window.state.currentLeads = [lead];
                        window.state.activeRunResult = { runId: id, target: pdb, pdbId: pdb, provenance: 'SIMULATED', leads: [lead], topLead: lead, screenedCount: 1, paretoCount: 1 };
                        pushRunHistory(window.state.activeRunResult);
                    }
                    renderRunHistoryStrip();
                    window.state.latestResistanceData = { evolved_smiles: 'CC(=O)Nc1ccc(F)cc1' };
                    adoptEvolvedScaffold();
                }"""
            )
            assert page.locator('#runHistoryStrip button').count() == 3
            assert page.locator('#workbenchSmilesInput').input_value() == 'CC(=O)Nc1ccc(F)cc1'
            page.locator('#runHistoryStrip button[data-arg="run-1"]').click()
            assert page.evaluate("window.state.runId") == "run-1"

            # 6. Static exports trigger downloads with zero 404s
            with page.expect_download() as dl_csv:
                page.locator('[data-action="export-leads-csv"]').click()
            assert dl_csv.value.suggested_filename.endswith("_leads.csv")

            with page.expect_download() as dl_md:
                page.locator('[data-action="download-dossier"]').click()
            assert dl_md.value.suggested_filename.endswith(".md")

            assert json.loads(page.evaluate("sessionStorage.getItem('bionemo_run_history_lite')")).__len__() == 3
            assert http_404s == [], f"Unexpected 404 responses: {http_404s}"
            assert console_errors == [], f"Unexpected console errors: {console_errors}"
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
