"""
TDD verification tests for Task 3: 3D PosePlausibilityValidator & multi-pose docking output.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import math

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Geometry import Point3D

from bionemo_benchmark.agents.docking_agent import BiophysicsDockingAgent
from bionemo_benchmark.core.models import MoleculeCandidate, TargetProfile
from bionemo_benchmark.domain.pose_validation import PosePlausibilityValidator


def _make_3d_sdf(
    smiles: str, perturb_atom: tuple[int, tuple[float, float, float]] | None = None
) -> str:
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    AllChem.EmbedMolecule(mol, randomSeed=42)
    AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    if perturb_atom is not None:
        idx, delta = perturb_atom
        conf = mol.GetConformer()
        p = conf.GetAtomPosition(idx)
        conf.SetAtomPosition(idx, Point3D(p.x + delta[0], p.y + delta[1], p.z + delta[2]))
    return Chem.MolToMolBlock(mol)


def test_pose_plausibility_good_pose_vs_ring_and_clash_failures() -> None:
    validator = PosePlausibilityValidator()

    good_sdf = _make_3d_sdf("O=C(N)c1ccccc1")
    res_good = validator.validate_pose(
        pose_sdf=good_sdf,
        pdb_text="ATOM      1  CA  ALA A  10      25.000  25.000  25.000  1.00 20.00           C\nEND\n",
        covalent_residue=None,
    )
    assert res_good["passes_all"] is True
    assert res_good["receptor_clash_count"] == 0
    assert res_good["planarity_pass"] is True
    assert res_good["strain_energy_kcal_mol"] is not None
    assert math.isfinite(res_good["strain_energy_kcal_mol"])

    # Receptor PDB with HETATM at origin + MODEL 2 at origin + altLoc 'B' at origin -> MUST be ignored!
    filtered_pdb = (
        "MODEL        1\n"
        "ATOM      1  CA  ALA A  10      25.000  25.000  25.000  1.00 20.00           C\n"
        "ATOM      2  CB BALA A  11       0.000   0.000   0.000  0.50 20.00           C\n"
        "HETATM    3  C1  LIG A 200       0.000   0.000   0.000  1.00 20.00           C\n"
        "ENDMDL\n"
        "MODEL        2\n"
        "ATOM      4  CA  GLY A  11       0.000   0.000   0.000  1.00 20.00           C\n"
        "ENDMDL\n"
    )
    res_filtered = validator.validate_pose(pose_sdf=good_sdf, pdb_text=filtered_pdb)
    assert res_filtered["receptor_clash_count"] == 0

    # Distort one ring carbon heavily out of plane + stretch bond -> must fail bond & planarity checks
    bad_sdf = _make_3d_sdf("O=C(N)c1ccccc1", perturb_atom=(5, (0.0, 0.0, 1.5)))
    res_bad = validator.validate_pose(pose_sdf=bad_sdf, pdb_text=filtered_pdb)
    assert res_bad["passes_all"] is False
    assert res_bad["planarity_pass"] is False or res_bad["bond_geometry_pass"] is False

    # Covalent residue proximity (<2.2A) annotated instead of hard clash when matching covalent_residue
    cys_pdb = "ATOM      1  SG  CYS A  12       0.500   0.000   0.000  1.00 20.00           S\nEND\n"
    res_cov = validator.validate_pose(
        pose_sdf=good_sdf, pdb_text=cys_pdb, covalent_residue="Cys12"
    )
    assert res_cov["covalent_proximity"] is True


def test_docking_agent_populates_multipose_and_plausibility() -> None:
    agent = BiophysicsDockingAgent(mock=True)
    target = TargetProfile(
        name="KRAS G12D",
        gene="KRAS",
        uniprot_id="P01116",
        pdb_id="7RPZ",
        description="KRAS G12D pocket",
        canonical_sequence="MTEYKLVVVGADGVGKSALTIQLIQNHFVDEYDPTIEDSY",
        pocket_residues=["Asp12", "Gln61", "Tyr96"],
        reference_ligand_name="MRTX1133",
        reference_ligand_smiles="O=C(N)c1ccccc1",
        pdb_text="ATOM      1  CA  ASP A  12      10.000  10.000  10.000  1.00 20.00           C\nEND\n",
    )
    cands = [
        MoleculeCandidate(
            id="L-1",
            smiles="O=C(Nc1ccccc1)c1ccncc1",
            parent_smiles="O=C(N)c1ccccc1",
            admet_verdict="PASS",
        )
    ]
    docked, _msg = agent.dock_candidates(cands, target)
    assert len(docked) == 1
    assert isinstance(docked[0].poses, list) and len(docked[0].poses) >= 1
    assert isinstance(docked[0].pose_validation, dict)
    assert "passes_all" in docked[0].pose_validation
    assert docked[0].poses[0].get("provenance") in (
        "MOCK_POCKET_APPROX",
        "UNBOUND_MOCK",
        "LIVE_NIM",
    )
