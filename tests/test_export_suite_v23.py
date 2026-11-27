"""Real-parser round-trip verification for all 6 v2.3.0 Cockpit export formats."""

from __future__ import annotations

import ast
import csv
import io
import json
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from rdkit import Chem
from rdkit.Chem import AllChem

from bionemo_benchmark.core.models import RetrosynthesisPlan, RetrosynthesisStep
from bionemo_benchmark.domain.robot_protocol import generate_ot2_protocol
from bionemo_benchmark.server.app import app

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


def _make_3d_sdf(smiles: str) -> str:
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    return Chem.MolToMolBlock(mol) + "$$$$\n"


def test_backend_full_cohort_pdf_and_xml_escape() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/dossier/pdf",
        json={
            "dossier": {
                "target": "KRAS G12D <Switch-II & Pocket>",
                "pdb_id": "7RPZ",
                "nominated_lead": "LEAD-01",
                "binding_affinity": -9.5,
                "screened": 2,
                "pareto_count": 2,
                "leads": [
                    {
                        "id": "LEAD-01",
                        "smiles": "CC(=O)Nc1ccc(O)cc1",
                        "mw": 151.16,
                        "logp": 0.9,
                        "qed": 0.72,
                        "sascore": 1.8,
                        "admet_verdict": "PASS",
                    },
                    {
                        "id": "LEAD-02",
                        "smiles": "Fc1ccc(NC(=O)C)cc1",
                        "mw": 153.15,
                        "logp": 1.4,
                        "qed": 0.75,
                        "sascore": 1.9,
                        "admet_verdict": "PASS",
                    },
                ],
                "pose_validation": {
                    "passes_all": True,
                    "receptor_clash_count": 0,
                    "strain_energy_kcal_mol": 1.4,
                },
                "interaction_contacts": [
                    {"type": "H-Bond & Salt", "residue": "ASP12<A>", "distance_a": 2.15}
                ],
                "baseline_diffs": [
                    {"lead_id": "LEAD-01", "original_affinity": -9.0, "current_affinity": -9.5}
                ],
                "retrosynthesis": {
                    "num_steps": 1,
                    "feasibility": "Heuristic BRICS / Literature Precedent",
                    "steps": [
                        {
                            "step": 1,
                            "reaction_type": "Amide Coupling",
                            "reagents": ["HATU", "DIPEA"],
                            "yield_pct": 85.0,
                            "difficulty": "Heuristic",
                        }
                    ],
                },
            }
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")


def test_backend_ot2_cwe94_and_epistemic_hygiene() -> None:
    malicious_step = RetrosynthesisStep(
        step_number=1,
        reaction_type='Amide """; import os; os.system("echo pwn") #',
        reaction_smarts="",
        reactants=[{"name": "X\nimport sys"}],
        reagents=["HATU"],
        product_smiles="CC(=O)Nc1ccc(O)cc1",
        estimated_yield_pct=85.0,
        difficulty="Heuristic",
    )
    plan = RetrosynthesisPlan(
        candidate_id='LEAD"""; import os #',
        target_smiles="CC(=O)Nc1ccc(O)cc1",
        num_steps=1,
        overall_feasibility="Heuristic BRICS / Literature Precedent",
        steps=[malicious_step],
        starting_materials=["Heuristic Terminal Fragment A"],
    )
    py_code = generate_ot2_protocol(plan)
    tree = ast.parse(py_code)
    top_imports = [
        n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    assert not any(
        isinstance(n, ast.Import) and any(a.name == "os" for a in n.names)
        for n in top_imports
    )
    assert "Commercially Accessible" not in py_code
    assert "Liquid-Handling Plate Setup Only" in py_code
    assert not re.search(r"[\U0001F300-\U0001FAFF\u26A0]", py_code)


def test_playwright_all_six_export_formats_round_trip(tmp_path: Path) -> None:
    sdf_pose_1 = _make_3d_sdf("CC(=O)Nc1ccc(O)cc1")
    sdf_pose_2 = _make_3d_sdf("Fc1ccc(NC(=O)C)cc1")

    server, port = _start_static_server()
    base_url = f"http://127.0.0.1:{port}/cockpit.html"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900}, accept_downloads=True
            )
            page = context.new_page()
            page.add_init_script("localStorage.setItem('bionemo_guide_seen', 'true');")
            page.goto(base_url, wait_until="networkidle")
            page.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")

            page.evaluate(
                """async ([sdf1, sdf2]) => {
                    const { renderLeads, selectLead } = await import('./js/cockpit/ui-controls.js');
                    const leads = [
                        {
                            id: 'LEAD-01',
                            smiles: 'CC(=O)Nc1ccc(O)cc1',
                            affinity: -9.50,
                            qed: 0.782,
                            sascore: 1.92,
                            mw: 151.16,
                            pareto: true,
                            verdict: 'PASS',
                            gi_absorption_high: true,
                            bbb_permeable: false,
                            pains_alerts: [],
                            brenk_alerts: [],
                            provenance: 'SIMULATED',
                            pose_sdf: sdf1,
                            poses: [
                                { rank: 1, sdf_data: sdf1, predicted_affinity_kcal_mol: -9.50, provenance: 'SIMULATED', pose_validation: { passes_all: true, receptor_clash_count: 0, strain_energy_kcal_mol: 1.2 } },
                                { rank: 2, sdf_data: sdf2, predicted_affinity_kcal_mol: -8.80, provenance: 'SIMULATED', pose_validation: { passes_all: true, receptor_clash_count: 0, strain_energy_kcal_mol: 1.8 } }
                            ],
                            interaction_contacts: [{ type: 'HBond', residue: 'Asp12', distance_a: 2.8 }],
                            pose_validation: { passes_all: true, bond_geometry_pass: true, receptor_clash_pass: true, receptor_clash_count: 0, planarity_pass: true, strain_energy_kcal_mol: 1.2 }
                        },
                        {
                            id: '=SUM(A1)',
                            smiles: 'Fc1ccc(NC(=O)C)cc1',
                            affinity: -8.42,
                            qed: 0.740,
                            sascore: 2.10,
                            mw: 153.15,
                            pareto: false,
                            verdict: 'PASS',
                            provenance: 'SIMULATED'
                        }
                    ];
                    window.state.runId = 'run-v23';
                    window.state.currentLeads = leads;
                    window.state.activeRunResult = {
                        runId: 'run-v23',
                        target: 'KRAS G12D',
                        pdbId: '7RPZ',
                        provenance: 'SIMULATED',
                        leads,
                        topLead: leads[0],
                        screenedCount: 2,
                        paretoCount: 1,
                        retrosynthesis: {
                            num_steps: 1,
                            feasibility: 'Heuristic BRICS / Literature Precedent',
                            steps: [{ step: 1, reaction_type: 'Amide Coupling', reagents: ['HATU', 'DIPEA'], yield_pct: 85, difficulty: 'Heuristic' }]
                        }
                    };
                    renderLeads();
                    selectLead(0);
                }""",
                [sdf_pose_1, sdf_pose_2],
            )

            # 1. JSON
            with page.expect_download() as dl_json:
                page.locator('[data-action="export-run-json"]').click()
            json_path = tmp_path / dl_json.value.suggested_filename
            dl_json.value.save_as(json_path)
            parsed_json = json.loads(json_path.read_text(encoding="utf-8"))
            assert parsed_json["schema_version"] == "2.3.0"
            assert "_baseline" not in json_path.read_text(encoding="utf-8")
            assert "NVIDIA Corporation" in parsed_json["legal_notice"]

            # 2. CSV
            with page.expect_download() as dl_csv:
                page.locator('[data-action="export-leads-csv"]').click()
            csv_path = tmp_path / dl_csv.value.suggested_filename
            dl_csv.value.save_as(csv_path)
            csv_raw = csv_path.read_bytes()
            assert csv_raw.startswith(b"\xef\xbb\xbf")
            rows = list(csv.DictReader(io.StringIO(csv_raw.decode("utf-8-sig"))))
            assert len(rows[0].keys()) == 21
            assert float(rows[0]["affinity_kcal_mol"]) == -9.50
            assert rows[1]["lead_id"] == "'=SUM(A1)"

            # 3. Multi-pose SDF parsed via RDKit
            with page.expect_download() as dl_sdf:
                page.locator('[data-action="download-sdf"]').click()
            sdf_path = tmp_path / dl_sdf.value.suggested_filename
            dl_sdf.value.save_as(sdf_path)
            suppl = Chem.ForwardSDMolSupplier(str(sdf_path), removeHs=False)
            mols = [m for m in suppl if m is not None]
            assert len(mols) == 2
            assert mols[0].GetProp("POSE_RANK") == "1"
            assert mols[1].GetProp("POSE_RANK") == "2"

            # 4. Headerless SMI parsed via RDKit
            with page.expect_download() as dl_smi:
                page.locator('[data-action="export-smiles"]').click()
            smi_path = tmp_path / dl_smi.value.suggested_filename
            dl_smi.value.save_as(smi_path)
            smi_suppl = Chem.SmilesMolSupplier(str(smi_path), delimiter="\t", titleLine=False)
            smi_mols = [m for m in smi_suppl if m is not None]
            assert len(smi_mols) == 2

            # 5. Markdown Dossier
            with page.expect_download() as dl_md:
                page.locator('[data-action="download-dossier"]').click()
            md_path = tmp_path / dl_md.value.suggested_filename
            dl_md.value.save_as(md_path)
            md_text = md_path.read_text(encoding="utf-8")
            assert "## 1. Executive KPIs" in md_text
            assert "## 6. License & Legal Attribution" in md_text

            # 6. Static Printable HTML Dossier (no <script>, no on*=)
            with page.expect_download() as dl_html:
                page.locator('[data-action="generate-ind-pdf"]').click()
            html_path = tmp_path / dl_html.value.suggested_filename
            dl_html.value.save_as(html_path)
            html_text = html_path.read_text(encoding="utf-8")
            assert "<script" not in html_text.lower()
            assert not re.search(r"\son[a-z]+\s*=", html_text, re.I)
            assert "@media print" in html_text

            # 7. Static OT-2 .py parsed via ast.parse
            page.locator('[data-action="robot-protocol"]').click()
            with page.expect_download() as dl_py:
                page.locator('[data-action="download-ot2-py"]').click()
            py_path = tmp_path / dl_py.value.suggested_filename
            dl_py.value.save_as(py_path)
            py_text = py_path.read_text(encoding="utf-8")
            ast.parse(py_text)
            assert "Amide Coupling" in py_text
            assert not re.search(r"[\U0001F300-\U0001FAFF\u26A0]", py_text)

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
