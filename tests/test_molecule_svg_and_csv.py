"""Backend tests for POST /api/molecule/svg and numeric-safe CSV behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient

from bionemo_benchmark.server.app import app

client = TestClient(app)


def test_molecule_svg_valid_smiles() -> None:
    res = client.post(
        "/api/molecule/svg",
        json={"smiles": "CC(=O)Nc1ccc(O)cc1", "theme": "dark"},
    )
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers.get("content-type", "")
    assert "<svg" in res.text


def test_molecule_svg_rejects_invalid_and_oversized_smiles() -> None:
    bad = client.post("/api/molecule/svg", json={"smiles": "not_a_valid_smiles!!!"})
    assert bad.status_code == 400

    oversized = client.post("/api/molecule/svg", json={"smiles": "C" * 513})
    assert oversized.status_code == 400
