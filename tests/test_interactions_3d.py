"""
TDD verification tests for Task 4: Directional 3D Protein-Ligand InteractionProfiler.
Tests H-bonds, salt bridges, hydrophobic contacts, pi-stacking, halogen bonds,
and negative geometry controls. Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

from bionemo_benchmark.domain.interactions import InteractionProfiler


def _sdf_from_atoms(title: str, atoms: list[tuple[str, float, float, float]], bonds: list[tuple[int, int, int]]) -> str:
    """Builds a minimal deterministic V2000 SDF block with explicit 3D coordinates."""
    lines = [
        title,
        "  RDKit          3D",
        "",
        f"{len(atoms):3d}{len(bonds):3d}  0  0  0  0  0  0  0  0999 V2000",
    ]
    for sym, x, y, z in atoms:
        lines.append(
            f"{x:10.4f}{y:10.4f}{z:10.4f} {sym:<3s} 0  0  0  0  0  0  0  0  0  0  0  0"
        )
    for a1, a2, order in bonds:
        lines.append(f"{a1:3d}{a2:3d}{order:3d}  0")
    lines.extend(["M  END", "$$$$"])
    return "\n".join(lines) + "\n"


def test_hbond_and_salt_bridge_and_hydrophobic_detection() -> None:
    profiler = InteractionProfiler()

    # Ligand: aminobutanol: N(1)-C(2)-C(3)-C(4)-O(5) where C(3) has only C neighbors (true hydrophobe)
    lig_sdf = _sdf_from_atoms(
        "test_lig",
        [
            ("N", 0.0, 0.0, 0.0),   # basic amine / salt-bridge cation / HBD
            ("C", 1.5, 0.0, 0.0),
            ("C", 3.0, 0.0, 0.0),   # true hydrophobic carbon (C-C-C)
            ("C", 4.4, 0.0, 0.0),
            ("O", 5.8, 0.0, 0.0),   # HBA / HBD
        ],
        [(1, 2, 1), (2, 3, 1), (3, 4, 1), (4, 5, 1)],
    )
    rec_pdb = (
        # ASP 12 OD1 3.1A from ligand N(0,0,0) -> Salt bridge + H-bond
        "ATOM      1  OD1 ASP A  12       0.000   3.100   0.000  1.00 20.00           O\n"
        # LEU 45 CD1 3.8A from ligand C3(3.0,0,0) -> Hydrophobic
        "ATOM      2  CD1 LEU A  45       3.000   3.800   0.000  1.00 20.00           C\n"
        # SER 60 OG 2.9A from ligand O5(5.8,0,0) -> H-bond
        "ATOM      3  OG  SER A  60       8.700   0.000   0.000  1.00 20.00           O\n"
        "END\n"
    )
    contacts = profiler.profile_interactions(lig_sdf, rec_pdb)
    types = {c["type"] for c in contacts}
    assert "H-Bond" in types
    assert "Salt Bridge" in types
    assert "Hydrophobic" in types
    for c in contacts:
        assert len(c["lig_coords"]) == 3
        assert len(c["rec_coords"]) == 3
        assert c["distance_a"] > 0.0


def test_pi_stacking_and_halogen_bond_geometry_controls() -> None:
    profiler = InteractionProfiler()

    # Planar benzene ring at z=0 centered at (0,0,0) + attached C7-Cl8 along +x axis
    # C1..C6 benzene with radius 1.4A in XY plane, C1=(1.4,0,0), Cl7=(3.1,0,0)
    import math

    atoms = []
    for k in range(6):
        ang = k * math.pi / 3.0
        atoms.append(("C", 1.4 * math.cos(ang), 1.4 * math.sin(ang), 0.0))
    atoms.append(("Cl", 3.1, 0.0, 0.0))  # bonded to atom 1 at (1.4, 0, 0) -> C1-Cl vector along +X
    bonds = [(1, 2, 2), (2, 3, 1), (3, 4, 2), (4, 5, 1), (5, 6, 2), (6, 1, 1), (1, 7, 1)]
    lig_sdf = _sdf_from_atoms("chlorobenzene", atoms, bonds)

    # Receptor PHE 80 ring parallel at z=3.9A + THR 90 OG1 collinear at x=6.2A (angle ~180 deg, dist 3.1A)
    phe_coords = [
        ("CG", 1.4, 0.0, 3.9),
        ("CD1", 0.7, 1.21, 3.9),
        ("CE1", -0.7, 1.21, 3.9),
        ("CZ", -1.4, 0.0, 3.9),
        ("CE2", -0.7, -1.21, 3.9),
        ("CD2", 0.7, -1.21, 3.9),
    ]
    pdb_lines = [
        f"ATOM  {i:5d}  {name:<3s} PHE A  80    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C"
        for i, (name, x, y, z) in enumerate(phe_coords, start=1)
    ]
    pdb_lines.append(
        "ATOM      7  OG1 THR A  90       6.200   0.000   0.000  1.00 20.00           O"
    )
    pdb_lines.append("END")
    contacts_good = profiler.profile_interactions(lig_sdf, "\n".join(pdb_lines) + "\n")
    types_good = {c["type"] for c in contacts_good}
    assert "Pi-Stacking" in types_good
    assert "Halogen Bond" in types_good

    # Negative control: THR 90 OG1 at 90 deg angle (x=3.1, y=3.1, z=0) -> distance 3.1A, angle ~90 deg -> NO halogen bond!
    bad_xbond_pdb = (
        "ATOM      1  OG1 THR A  90       3.100   3.100   0.000  1.00 20.00           O\nEND\n"
    )
    contacts_bad = profiler.profile_interactions(lig_sdf, bad_xbond_pdb)
    assert all(c["type"] != "Halogen Bond" for c in contacts_bad)
