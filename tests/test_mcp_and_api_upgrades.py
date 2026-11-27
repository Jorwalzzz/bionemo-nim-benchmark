"""
TDD verification tests for Task 7: FastAPI JSON upgrade fields, strict allow_nan=False,
and 3 new byte/length-guarded BioNeMo MCP tools.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from bionemo_benchmark.mcp.server import (
    bionemo_plan_retrosynthesis,
    bionemo_screen_medchem,
    bionemo_validate_pose,
)
from bionemo_benchmark.server.app import app

_HOST_HEADERS = {"Origin": "http://localhost:8000", "X-Requested-With": "XMLHttpRequest"}


def test_mcp_medchem_pose_validation_and_retrosynthesis_tools_with_caps() -> None:
    # 1. bionemo_screen_medchem
    ok_med = bionemo_screen_medchem("CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21")
    assert ok_med["valid"] is True
    assert "brenk_alerts" in ok_med
    assert ok_med["gi_absorption_high"] is True
    assert ok_med["bbb_permeable"] is True
    json.dumps(ok_med, allow_nan=False)

    oversized_smi = bionemo_screen_medchem("C" * 2049)
    assert oversized_smi["valid"] is False

    # 2. bionemo_validate_pose (caps: 1 MB SDF, 5 MB PDB)
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1"))
    AllChem.EmbedMolecule(mol, randomSeed=42)
    sdf = Chem.MolToMolBlock(mol)
    pdb = "ATOM      1  CA  ALA A  10      25.000  25.000  25.000  1.00 20.00           C\nEND\n"

    ok_pose = bionemo_validate_pose(pose_sdf=sdf, pdb_text=pdb)
    assert ok_pose["valid"] is True
    assert ok_pose["pose_validation"]["passes_all"] is True
    assert isinstance(ok_pose["interaction_contacts"], list)
    json.dumps(ok_pose, allow_nan=False)

    too_big_sdf = bionemo_validate_pose(pose_sdf="A" * 1_048_577, pdb_text=pdb)
    assert too_big_sdf["valid"] is False

    too_big_pdb = bionemo_validate_pose(pose_sdf=sdf, pdb_text="A" * 5_242_881)
    assert too_big_pdb["valid"] is False

    # 3. bionemo_plan_retrosynthesis
    ok_retro = bionemo_plan_retrosynthesis("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCC1CCN(C)CC1")
    assert ok_retro["valid"] is True
    assert isinstance(ok_retro["route_tree"], dict)
    assert ok_retro["route_tree"]["depth"] == 0
    json.dumps(ok_retro, allow_nan=False)


def test_fastapi_run_and_redock_expose_v23_fields_without_nan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("NIM_API_KEY_REQUIRED", "false")
    client = TestClient(app)

    run_resp = client.post(
        "/api/run",
        json={"target": "KRAS G12D", "max_rounds": 1, "num_candidates": 4},
        headers=_HOST_HEADERS,
    )
    assert run_resp.status_code == 200
    payload = run_resp.json()
    json.dumps(payload, allow_nan=False)

    assert payload["leads"], "Expected at least one lead in /api/run response"
    lead = payload["leads"][0]
    assert "brenk_alerts" in lead
    assert "gi_absorption_high" in lead
    assert "pose_validation" in lead
    assert "interaction_contacts" in lead
    assert "poses" in lead and isinstance(lead["poses"], list)
    assert "route_tree" in payload["retrosynthesis"]
    assert "is_convergent" in payload["retrosynthesis"]

    redock_resp = client.post(
        "/api/redock",
        json={"smiles": "COc1ccc(C(=O)Nc2cccc(Cl)c2)cc1", "target": "KRAS G12D"},
        headers=_HOST_HEADERS,
    )
    assert redock_resp.status_code == 200
    r_data = redock_resp.json()
    json.dumps(r_data, allow_nan=False)
    assert "pose_validation" in r_data
    assert "interaction_contacts" in r_data
    assert "poses" in r_data
    assert "route_tree" in r_data["retrosynthesis"]
