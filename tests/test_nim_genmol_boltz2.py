"""
TDD verification tests for Task 2: NIM GenMol & Boltz-2 adapters, NVCF 202 polling,
DiffDock nested list parsing, and target-agnostic bioisostere scaffold mutation.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from rdkit import Chem

from bionemo_benchmark.agents.generative_chemist import GenerativeChemistAgent
from bionemo_benchmark.core.client import (
    Boltz2Response,
    GenMolResponse,
    NimBioClient,
)
from bionemo_benchmark.core.models import TargetProfile


def test_genmol_and_boltz2_mock_adapters() -> None:
    client = NimBioClient(mock=True)

    gen = client.generate_genmol("c1ccccc1C(=O)N", num_molecules=4)
    assert isinstance(gen, GenMolResponse)
    assert gen.is_mock is True
    assert len(gen.molecules) == 4
    for item in gen.molecules:
        assert Chem.MolFromSmiles(item["smiles"]) is not None

    b2 = client.predict_boltz2_complex("MTEYKLVVVGAGGVGKSALTIQLIQ", "COc1ccc(CCNC(=O)c2ccncc2)cc1")
    assert isinstance(b2, Boltz2Response)
    assert b2.is_mock is True
    assert b2.complex_plddt is not None and 0.0 <= b2.complex_plddt <= 1.0
    assert "ATOM" in b2.structure_pdb or "_atom_site" in b2.structure_mmcif


def test_nvcf_202_async_polling_and_batch_diffdock_parsing(monkeypatch) -> None:
    client = NimBioClient(api_key="unit-test-token-0000", mock=False)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    resp_202 = MagicMock()
    resp_202.status_code = 202
    resp_202.headers = {"nvcf-reqid": "req-abc-123"}
    resp_202.content = b""
    resp_202.json.return_value = {"status": "pending"}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.headers = {"nv-request-id": "req-abc-123"}
    resp_200.content = b"{}"
    resp_200.json.return_value = {
        "structures": [{"format": "mmcif", "structure": "data_boltz2\nloop_\n_atom_site.id\n"}],
        "confidence_scores": [0.89],
        "complex_plddt": 0.89,
        "ptm": 0.84,
    }

    calls: list[tuple[str, str]] = []

    def fake_request(method: str, url: str, **_kwargs):
        calls.append((method, url))
        if method == "POST":
            return resp_202
        return resp_200

    monkeypatch.setattr(client.session, "request", fake_request)
    res = client.predict_boltz2_complex("MTEYKLVVVGAGGVGKSALTIQLIQ", "CCO")
    assert res.is_mock is False
    assert res.complex_plddt == 0.89
    assert len(calls) == 2
    assert calls[1][0] == "GET"
    assert "req-abc-123" in calls[1][1]

    # Batch DiffDock nested list parsing (e.g. position_confidence: [[-0.4, -1.1]])
    diffdock_200 = MagicMock()
    diffdock_200.status_code = 200
    diffdock_200.headers = {"x-request-id": "dd-batch-1"}
    diffdock_200.content = b"{}"
    diffdock_200.json.return_value = {
        "status": "success",
        "position_confidence": [[-0.25, -1.10]],
        "ligand_positions": [["pose1_sdf", "pose2_sdf"]],
    }
    monkeypatch.setattr(client.session, "request", lambda **_kw: diffdock_200)
    dd = client.dock_complex("MTEYKLVVVGAGGVGKSALTIQLIQ", "CCO", num_poses=2)
    assert dd.is_mock is False
    assert dd.num_poses == 2
    assert dd.poses[0].confidence_score == -0.25
    assert dd.poses[1].sdf_data == "pose2_sdf"


def test_target_agnostic_bioisostere_mutator() -> None:
    chemist = GenerativeChemistAgent(client=NimBioClient(mock=True))
    unseen_target = TargetProfile(
        name="Unseen Kinase X9",
        gene="NOVELX9",
        uniprot_id="P0CG48",
        pdb_id="1UBQ",
        description="Unseen benchmark protein target",
        canonical_sequence="MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG",
        pocket_residues=["Lys48", "Ile44"],
        reference_ligand_name="RefLig-X9",
        reference_ligand_smiles="COc1ccc(C(=O)Nc2cccc(Cl)c2)cc1",
    )
    candidates, _msg = chemist.generate_derivatives(unseen_target, num_candidates=5)
    assert len(candidates) >= 3
    smiles_set = {c.smiles for c in candidates}
    assert len(smiles_set) >= 2
    for c in candidates:
        assert Chem.MolFromSmiles(c.smiles) is not None
