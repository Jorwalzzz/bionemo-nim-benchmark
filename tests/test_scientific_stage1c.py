"""
Stage 1C Scientific Integrity Regression Suite.

Covers:
1. Verified RCSB PDB / UniProt sequences and key mutant/catalytic motifs across data/sample_complexes.json.
2. Strict separation between KRAS G12D (7RPZ) and KRAS G12C (6OIM covalent Cys12) vs WT KRAS (8AZV).
3. Unforgeable Pydantic v2 StageProvenance / CampaignProvenance invariants & ReportLab watermark.
4. Real RDKit BRICS retrosynthetic disconnections and pocket-centered docking conformers.
5. Deterministic ResistanceEscapeEngine seeding and corrected 10,000-complex campaign speedup math.
"""

from __future__ import annotations

import base64
import json
import re
import zlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from rdkit import Chem

from bionemo_benchmark.agents.docking_agent import BiophysicsDockingAgent
from bionemo_benchmark.agents.generative_chemist import GenerativeChemistAgent
from bionemo_benchmark.agents.resistance_engine import ResistanceEscapeEngine
from bionemo_benchmark.agents.retrosynthesis_agent import RetrosynthesisAgent
from bionemo_benchmark.agents.target_scout import TARGET_REGISTRY, TargetScoutAgent
from bionemo_benchmark.core.models import MoleculeCandidate
from bionemo_benchmark.core.provenance import (
    CampaignProvenance,
    ExecutionMode,
    StageProvenance,
    StageStatus,
)
from bionemo_benchmark.reporting.ind_dossier import generate_ind_pdf
from bionemo_benchmark.reporting.nvidia_showcase import GreenComputeProfiler
from bionemo_benchmark.server.app import app

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestVerifiedSampleComplexesAndPresets:
    """Verify scientific accuracy of target sequences, PDB IDs, UniProt IDs, and key motifs."""

    def test_sample_complexes_match_pdb_uniprot_and_motifs(self):
        complexes = json.loads((REPO_ROOT / "data" / "sample_complexes.json").read_text(encoding="utf-8"))
        by_id = {c["id"]: c for c in complexes}
        assert len(complexes) == 10

        expected_checks = {
            "complex_01": ("1UBQ", "P62988", "MQIFVKTLTGKT"),
            "complex_02": ("1DLS", "P00374", "VGSLNCIVAVSQ"),
            "complex_03": ("1IEP", "P00519", "KHKLGGGQYGEV"),
            "complex_04": ("1M17", "P00533", "LGSGAFGTVYKG"),
            "complex_05": ("7BV2", "P0DTD1", "SADAQSFLNRVC"),
            "complex_06": ("7BQY", "P0DTD1", "SGFRKMAFPSGK"),
            "complex_07": ("2ITZ", "P00533", "EAPNQALLRILK"),
            "complex_08": ("4KD1", "P24941", "MENFQKVEKIGEG"),
            "complex_09": ("5DS3", "P09874", "WHGSRTTNFAGIL"),
            "complex_10": ("6OIM", "P01116", "GACGVG"),
        }
        for cid, (pdb_id, uniprot_id, motif) in expected_checks.items():
            entry = by_id[cid]
            assert entry["pdb_id"] == pdb_id
            assert entry["uniprot_id"] == uniprot_id
            assert motif in entry["sequence"], f"{cid} ({pdb_id}) missing expected motif '{motif}'"
            assert Chem.MolFromSmiles(entry["smiles"]) is not None

        # Explicitly reject HER2/BRAF/WT-KRAS cross-contaminations
        assert "ERBB2" not in by_id["complex_08"]["target_name"]
        assert by_id["complex_09"]["pdb_id"] == "5DS3"
        assert by_id["complex_10"]["covalent_adduct"] is True
        assert by_id["complex_10"]["covalent_residue"] == "Cys12"
        assert "GAGGVG" not in by_id["complex_10"]["sequence"]
        assert "GADGVG" not in by_id["complex_10"]["sequence"]

    def test_kras_g12d_preset_uses_7rpz_not_8azv(self):
        kras = TARGET_REGISTRY["KRAS G12D"]
        assert kras["pdb_id"] == "7RPZ"
        assert "GADGVG" in kras["canonical_sequence"]
        assert "GAGGVG" not in kras["canonical_sequence"]


class TestUnforgeableProvenanceSchema:
    """Verify Pydantic provenance invariants prevent forged live claims and propagate to PDF."""

    def test_stage_provenance_rejects_forged_live_and_empty_fallback(self):
        with pytest.raises(ValidationError):
            StageProvenance(
                stage_name="diffdock",
                status=StageStatus.LIVE,
                http_status=500,
                endpoint_url="https://health.api.nvidia.com/v1/biology/mit/diffdock",
                nim_request_id="req-123",
            )

        with pytest.raises(ValidationError):
            StageProvenance(
                stage_name="molmim",
                status=StageStatus.LIVE,
                http_status=200,
                endpoint_url="",
                nim_request_id="req-123",
            )

        with pytest.raises(ValidationError):
            StageProvenance(
                stage_name="molmim",
                status=StageStatus.FALLBACK,
                fallback_reason=None,
            )

        with pytest.raises(ValidationError):
            StageProvenance(
                stage_name="esmfold",
                status=StageStatus.MOCK,
                nim_request_id="req-nim-forged",
            )

    def test_campaign_provenance_forbids_override_and_computes_modes(self):
        live_stage = StageProvenance(
            stage_name="molmim",
            status=StageStatus.LIVE,
            endpoint_url="https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate",
            http_status=200,
            nim_request_id="nv-live-001",
        )
        fallback_stage = StageProvenance(
            stage_name="diffdock",
            status=StageStatus.FALLBACK,
            fallback_reason="HTTP 503 upstream timeout",
        )
        mock_stage = StageProvenance(stage_name="esmfold", status=StageStatus.MOCK)

        with pytest.raises(ValidationError):
            CampaignProvenance(
                stages=(mock_stage,),
                backend_host="127.0.0.1",
                rdkit_version="2024.03.5",
                overall_mode="LIVE_NVIDIA_NIM",  # type: ignore[call-arg]
            )

        hybrid = CampaignProvenance(
            stages=(live_stage, fallback_stage),
            backend_host="127.0.0.1",
            rdkit_version="2024.03.5",
        )
        assert hybrid.overall_mode == ExecutionMode.HYBRID_FALLBACK
        assert hybrid.is_simulated is True
        assert hybrid.nim_endpoints_called == [
            "https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate"
        ]
        assert hybrid.request_ids == ["nv-live-001"]
        assert hybrid.pdf_watermark == "HYBRID NIM + HEURISTIC FALLBACK"

        all_live = CampaignProvenance(
            stages=(live_stage,),
            backend_host="127.0.0.1",
            rdkit_version="2024.03.5",
        )
        assert all_live.overall_mode == ExecutionMode.LIVE_NVIDIA_NIM
        assert all_live.is_simulated is False
        assert all_live.pdf_watermark == "VERIFIED NVIDIA NIM EXECUTION"

    def test_live_http_failure_produces_honest_fallback_and_pdf_watermark(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Force live mode with broken network to verify FALLBACK provenance rather than silent mock lie
        monkeypatch.setattr(
            "bionemo_benchmark.infra.security_sentinel.SafeSanitizer.safe_http_request",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("Simulated NIM outage")),
        )
        chem = GenerativeChemistAgent(api_key="nvapi-test-key", mock=False)
        cands, _ = chem.generate_derivatives("CCO", "KRAS G12D", num_molecules=3)
        assert len(cands) >= 1
        assert chem.last_stage_provenance is not None
        assert chem.last_stage_provenance.status == StageStatus.FALLBACK
        assert "RuntimeError" in (chem.last_stage_provenance.fallback_reason or "")

        pdf_bytes = generate_ind_pdf(
            {
                "target": "KRAS G12D",
                "pdb_id": "7RPZ",
                "nominated_lead": "LEAD-001",
                "binding_affinity": -9.2,
                "provenance": {"overall_mode": "LIVE_NVIDIA_NIM"},  # Unverified without stages -> downgraded!
            }
        )
        decoded_chunks: list[str] = []
        for match in re.finditer(rb"(?m)^stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL):
            raw = match.group(1).strip()
            if raw.endswith(b"~>"):
                raw = base64.a85decode(raw[:-2], adobe=False)
            try:
                decoded_chunks.append(zlib.decompress(raw).decode("latin1", errors="ignore"))
            except zlib.error:
                decoded_chunks.append(raw.decode("latin1", errors="ignore"))
        combined_pdf_text = "\n".join(decoded_chunks) + pdf_bytes.decode("latin1", errors="ignore")
        assert "HEURISTIC SIMULATION" in combined_pdf_text
        assert "PROVENANCE WATERMARK" in combined_pdf_text


class TestBRICSAndPocketDockingAndMath:
    """Verify real RDKit BRICS fragments, pocket-centered docking, seed stability, and 10x math."""

    def test_brics_retrosynthesis_produces_molecule_specific_synthons(self):
        retro = RetrosynthesisAgent()
        lead = MoleculeCandidate(
            id="LEAD-BRICS-01",
            smiles="O=C(Nc1ccc(Cl)cc1)c1cccnc1",
            parent_smiles="O=C(Nc1ccc(Cl)cc1)c1cccnc1",
        )
        plan = retro.plan_synthesis_route(lead)
        assert plan.num_steps >= 1
        assert "BRICS Retrosynthetic Disconnections" in plan.steps[0].reaction_type
        assert "Sigma-Aldrich" not in json.dumps([s.__dict__ for s in plan.steps])
        assert any("BRICS Synthon" in mat for mat in plan.starting_materials)

    def test_docking_centers_conformer_on_crystal_pocket_not_origin(self):
        scout = TargetScoutAgent(mock=True)
        target, _ = scout.scout_target("KRAS G12D")
        assert target.pdb_id == "7RPZ"

        docker = BiophysicsDockingAgent(mock=True)
        cand = MoleculeCandidate(
            id="LEAD-POCKET-01",
            smiles="O=C(Nc1ccc(F)cc1)c1ccccc1",
            parent_smiles="O=C(Nc1ccc(F)cc1)c1ccccc1",
            admet_verdict="PASS",
        )
        docked, _ = docker.dock_candidates([cand], target)
        mol = Chem.MolFromMolBlock(docked[0].pose_sdf)
        assert mol is not None
        conf = mol.GetConformer()
        cx = sum(conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()
        cy = sum(conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()
        cz = sum(conf.GetAtomPosition(i).z for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()

        dist_from_pocket = ((cx - 1.71) ** 2 + (cy - 4.93) ** 2 + (cz - (-23.16)) ** 2) ** 0.5
        assert dist_from_pocket < 1.5

    def test_resistance_engine_seed_determinism_and_10x_benchmark_math(self):
        target, _ = TargetScoutAgent(mock=True).scout_target("KRAS G12D")
        lead = MoleculeCandidate(id="L1", smiles="CCO", parent_smiles="CCO", binding_affinity=-9.0)
        e1 = ResistanceEscapeEngine(mock=True, seed=42).scan_and_evolve(lead, target)
        e2 = ResistanceEscapeEngine(mock=True, seed=42).scan_and_evolve(lead, target)
        assert e1.mutant_affinity == e2.mutant_affinity
        assert e1.evolved_affinity == e2.evolved_affinity
        assert e1.nim_calls_made == 0

        impact = GreenComputeProfiler.calculate_campaign_impact(
            cpu_time_sec=32.40, gpu_time_sec=0.55, num_molecules=10000
        )
        assert impact["basis"] == "Illustrative"
        # True 10,000-complex energy for 32.40s CPU @ 1.6kW = 144.0 kWh (previously 14.4 kWh 10x bug)
        assert abs(impact["cpu_energy_kwh"] - 144.0) < 0.2

        client = TestClient(app)
        resp = client.get("/api/benchmark/speedup")
        assert resp.status_code == 200
        d = resp.json()
        expected_saved = round(
            round((d["total_cpu_latency_sec"] * 10000) / 3600.0, 1)
            - round((d["total_h100_latency_sec"] * 10000) / 3600.0, 2),
            1,
        )
        assert d["time_saved_hours_10k_campaign"] == expected_saved
