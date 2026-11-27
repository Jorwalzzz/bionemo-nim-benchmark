"""
Directional 3D Protein-Ligand Non-Covalent Interaction Profiler.
Copyright (C) 2026 Jorwalzzz. Licensed under AGPL-3.0-only.

Detects:
- Hydrogen bonds (heavy <= 3.5 A; D-H...A >= 120 deg when explicit H present)
- Salt bridges (ionizable pairs <= 4.0 A)
- Hydrophobic contacts (apolar heavy atoms <= 4.5 A)
- Pi-stacking (aromatic centroids <= 5.5 A with ring plane normal angle)
- Halogen bonds (C-X...A for Cl/Br/I <= 3.8 A and sigma-hole angle >= 140 deg)
"""

from __future__ import annotations

import math
import os
from collections import defaultdict
from typing import Any

import numpy as np
from rdkit import Chem, RDConfig
from rdkit.Chem import ChemicalFeatures

from bionemo_benchmark.domain.pdb_utils import parse_pdb_heavy_atoms

_FEATURE_FACTORY: Any | None = None

_HBOND_DONOR_ATOMS: dict[str, set[str]] = {
    "ARG": {"N", "NE", "NH1", "NH2"},
    "ASN": {"N", "ND2"},
    "CYS": {"N", "SG"},
    "GLN": {"N", "NE2"},
    "HIS": {"N", "ND1", "NE2"},
    "LYS": {"N", "NZ"},
    "SER": {"N", "OG"},
    "THR": {"N", "OG1"},
    "TRP": {"N", "NE1"},
    "TYR": {"N", "OH"},
}

_HBOND_ACCEPTOR_ATOMS: dict[str, set[str]] = {
    "ASN": {"O", "OD1"},
    "ASP": {"O", "OD1", "OD2"},
    "CYS": {"O", "SG"},
    "GLN": {"O", "OE1"},
    "GLU": {"O", "OE1", "OE2"},
    "HIS": {"O", "ND1", "NE2"},
    "MET": {"O", "SD"},
    "SER": {"O", "OG"},
    "THR": {"O", "OG1"},
    "TYR": {"O", "OH"},
}

_POS_CHARGED_ATOMS: dict[str, set[str]] = {
    "ARG": {"NE", "NH1", "NH2"},
    "LYS": {"NZ"},
    "HIS": {"ND1", "NE2"},
}

_NEG_CHARGED_ATOMS: dict[str, set[str]] = {
    "ASP": {"OD1", "OD2"},
    "GLU": {"OE1", "OE2"},
}

_HYDROPHOBIC_RESIDUES: set[str] = {
    "ALA",
    "VAL",
    "LEU",
    "ILE",
    "MET",
    "PHE",
    "TRP",
    "PRO",
    "TYR",
}

_AROMATIC_RING_ATOMS: dict[str, set[str]] = {
    "PHE": {"CG", "CD1", "CD2", "CE1", "CE2", "CZ"},
    "TYR": {"CG", "CD1", "CD2", "CE1", "CE2", "CZ"},
    "HIS": {"CG", "ND1", "CD2", "CE1", "NE2"},
    "TRP": {"CG", "CD1", "NE1", "CE2", "CD2", "CE3", "CZ2", "CZ3", "CH2"},
}


def _get_feature_factory() -> Any | None:
    global _FEATURE_FACTORY
    if _FEATURE_FACTORY is not None:
        return _FEATURE_FACTORY
    fdef_path = os.path.join(RDConfig.RDDataDir, "BaseFeatures.fdef")
    if os.path.exists(fdef_path):
        _FEATURE_FACTORY = ChemicalFeatures.BuildFeatureFactory(fdef_path)
    return _FEATURE_FACTORY


def _angle_deg(a: np.ndarray, vertex: np.ndarray, b: np.ndarray) -> float:
    v1 = a - vertex
    v2 = b - vertex
    n1 = float(np.linalg.norm(v1))
    n2 = float(np.linalg.norm(v2))
    if n1 < 1e-6 or n2 < 1e-6:
        return 0.0
    cos_theta = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return math.degrees(math.acos(cos_theta))


def _round_coords(vec: np.ndarray) -> list[float]:
    return [round(float(vec[0]), 3), round(float(vec[1]), 3), round(float(vec[2]), 3)]


class InteractionProfiler:
    """Identifies 3D protein-ligand non-covalent interactions using geometric criteria."""

    def __init__(
        self,
        hbond_max_dist: float = 3.5,
        hbond_min_angle_deg: float = 120.0,
        salt_bridge_max_dist: float = 4.0,
        hydrophobic_max_dist: float = 4.5,
        pi_stack_max_dist: float = 5.5,
        halogen_max_dist: float = 3.8,
        halogen_min_angle_deg: float = 140.0,
    ):
        self.hbond_max_dist = hbond_max_dist
        self.hbond_min_angle_deg = hbond_min_angle_deg
        self.salt_bridge_max_dist = salt_bridge_max_dist
        self.hydrophobic_max_dist = hydrophobic_max_dist
        self.pi_stack_max_dist = pi_stack_max_dist
        self.halogen_max_dist = halogen_max_dist
        self.halogen_min_angle_deg = halogen_min_angle_deg
        self.factory = _get_feature_factory()

    @staticmethod
    def _group_receptor_residues(
        rec_atoms: list[dict[str, Any]],
    ) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for atom in rec_atoms:
            grouped[(atom["chain"], atom["resnum"], atom["resname"])].append(atom)
        return grouped

    def profile_interactions(
        self, pose_sdf: str, pdb_text: str, max_contacts: int = 32
    ) -> list[dict[str, Any]]:
        """Computes directional 3D contacts between a ligand SDF pose and a receptor PDB."""
        if not pose_sdf or not pose_sdf.strip() or not pdb_text or not pdb_text.strip():
            return []

        mol = Chem.MolFromMolBlock(pose_sdf, removeHs=False, sanitize=True)
        if mol is None or mol.GetNumConformers() == 0:
            return []

        rec_atoms = parse_pdb_heavy_atoms(pdb_text)
        if not rec_atoms:
            return []

        conf = mol.GetConformer()
        lig_xyz = np.array(
            [
                [
                    conf.GetAtomPosition(i).x,
                    conf.GetAtomPosition(i).y,
                    conf.GetAtomPosition(i).z,
                ]
                for i in range(mol.GetNumAtoms())
            ],
            dtype=float,
        )

        # Collect RDKit pharmacophore features on ligand
        lig_donors: list[int] = []
        lig_acceptors: list[int] = []
        lig_pos_atoms: list[int] = []
        lig_neg_atoms: list[int] = []
        lig_hydrophobes: list[int] = []
        lig_arom_rings: list[tuple[np.ndarray, np.ndarray]] = []

        if self.factory is not None:
            for feat in self.factory.GetFeaturesForMol(mol):
                fam = feat.GetFamily()
                atom_ids = [int(i) for i in feat.GetAtomIds()]
                if fam == "Donor":
                    lig_donors.extend(atom_ids)
                elif fam == "Acceptor":
                    lig_acceptors.extend(atom_ids)
                elif fam == "PosIonizable":
                    lig_pos_atoms.extend(atom_ids)
                elif fam == "NegIonizable":
                    lig_neg_atoms.extend(atom_ids)
                elif fam in ("Hydrophobe", "LumpedHydrophobe"):
                    lig_hydrophobes.extend(atom_ids)

        # Explicit chemical fallbacks for minimalist ligands & aromatic rings
        for atom in mol.GetAtoms():
            idx = atom.GetIdx()
            sym = atom.GetSymbol().upper()
            if sym in ("N", "O") and atom.GetTotalNumHs(includeNeighbors=True) > 0 and idx not in lig_donors:
                lig_donors.append(idx)
            if sym in ("N", "O") and idx not in lig_acceptors:
                lig_acceptors.append(idx)
            if sym == "N" and not atom.GetIsAromatic() and atom.GetDegree() <= 3:
                is_amide = any(
                    nbr.GetSymbol() == "C"
                    and any(
                        b.GetBondType() == Chem.BondType.DOUBLE
                        and b.GetOtherAtom(nbr).GetSymbol() == "O"
                        for b in nbr.GetBonds()
                    )
                    for nbr in atom.GetNeighbors()
                )
                if not is_amide and idx not in lig_pos_atoms:
                    lig_pos_atoms.append(idx)
            if sym == "C" and atom.GetAtomicNum() == 6:
                has_polar_nbr = any(
                    nbr.GetSymbol() in ("O", "N") for nbr in atom.GetNeighbors()
                )
                if not has_polar_nbr and idx not in lig_hydrophobes:
                    lig_hydrophobes.append(idx)

        for ring in mol.GetRingInfo().AtomRings():
            if len(ring) in (5, 6) and all(
                mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring
            ):
                pts = lig_xyz[list(ring)]
                centroid = pts.mean(axis=0)
                _, _, vt = np.linalg.svd(pts - centroid, full_matrices=False)
                lig_arom_rings.append((centroid, vt[-1]))

        lig_donors = list(dict.fromkeys(lig_donors))
        lig_acceptors = list(dict.fromkeys(lig_acceptors))
        lig_pos_atoms = list(dict.fromkeys(lig_pos_atoms))
        lig_neg_atoms = list(dict.fromkeys(lig_neg_atoms))
        lig_hydrophobes = list(dict.fromkeys(lig_hydrophobes))

        contacts_by_key: dict[tuple[str, str], dict[str, Any]] = {}

        def _record(contact: dict[str, Any]) -> None:
            key = (contact["type"], f"{contact['chain']}:{contact['residue']}")
            existing = contacts_by_key.get(key)
            if existing is None or contact["distance_a"] < existing["distance_a"]:
                contacts_by_key[key] = contact

        grouped = self._group_receptor_residues(rec_atoms)

        for (chain, resnum, resname), res_atoms in grouped.items():
            res_label = f"{resname.capitalize()}{resnum}"

            # Receptor aromatic rings for Pi-stacking
            arom_allowed = _AROMATIC_RING_ATOMS.get(resname)
            if arom_allowed and lig_arom_rings:
                ring_pts = [
                    [a["x"], a["y"], a["z"]]
                    for a in res_atoms
                    if a["atom_name"] in arom_allowed
                ]
                if len(ring_pts) >= 5:
                    pts_arr = np.array(ring_pts, dtype=float)
                    rec_cent = pts_arr.mean(axis=0)
                    _, _, vt = np.linalg.svd(pts_arr - rec_cent, full_matrices=False)
                    rec_norm = vt[-1]
                    for lig_cent, lig_norm in lig_arom_rings:
                        dist = float(np.linalg.norm(lig_cent - rec_cent))
                        if dist <= self.pi_stack_max_dist:
                            cos_n = float(np.clip(abs(np.dot(lig_norm, rec_norm)), 0.0, 1.0))
                            plane_ang = math.degrees(math.acos(cos_n))
                            if plane_ang <= 35.0 or plane_ang >= 55.0:
                                _record(
                                    {
                                        "type": "Pi-Stacking",
                                        "residue": res_label,
                                        "chain": chain,
                                        "atom_label": "RING",
                                        "lig_atom_label": "AROM",
                                        "distance_a": round(dist, 2),
                                        "angle_deg": round(plane_ang, 1),
                                        "lig_coords": _round_coords(lig_cent),
                                        "rec_coords": _round_coords(rec_cent),
                                    }
                                )

            for rec in res_atoms:
                rec_xyz = np.array([rec["x"], rec["y"], rec["z"]], dtype=float)
                aname = rec["atom_name"]
                elem = rec["element"]

                is_rec_donor = aname == "N" or aname in _HBOND_DONOR_ATOMS.get(resname, set())
                is_rec_acceptor = aname == "O" or aname in _HBOND_ACCEPTOR_ATOMS.get(resname, set())
                is_rec_pos = aname in _POS_CHARGED_ATOMS.get(resname, set())
                is_rec_neg = aname in _NEG_CHARGED_ATOMS.get(resname, set())
                is_rec_hydrophobic = (
                    resname in _HYDROPHOBIC_RESIDUES
                    and elem in ("C", "S")
                    and aname not in ("N", "CA", "C", "O")
                )

                # Salt Bridges
                if is_rec_neg:
                    for idx in lig_pos_atoms:
                        dist = float(np.linalg.norm(lig_xyz[idx] - rec_xyz))
                        if dist <= self.salt_bridge_max_dist:
                            _record(
                                {
                                    "type": "Salt Bridge",
                                    "residue": res_label,
                                    "chain": chain,
                                    "atom_label": aname,
                                    "lig_atom_label": f"{mol.GetAtomWithIdx(idx).GetSymbol()}{idx + 1}",
                                    "distance_a": round(dist, 2),
                                    "angle_deg": None,
                                    "lig_coords": _round_coords(lig_xyz[idx]),
                                    "rec_coords": _round_coords(rec_xyz),
                                }
                            )
                if is_rec_pos:
                    for idx in lig_neg_atoms:
                        dist = float(np.linalg.norm(lig_xyz[idx] - rec_xyz))
                        if dist <= self.salt_bridge_max_dist:
                            _record(
                                {
                                    "type": "Salt Bridge",
                                    "residue": res_label,
                                    "chain": chain,
                                    "atom_label": aname,
                                    "lig_atom_label": f"{mol.GetAtomWithIdx(idx).GetSymbol()}{idx + 1}",
                                    "distance_a": round(dist, 2),
                                    "angle_deg": None,
                                    "lig_coords": _round_coords(lig_xyz[idx]),
                                    "rec_coords": _round_coords(rec_xyz),
                                }
                            )

                # H-Bonds (Ligand Donor -> Receptor Acceptor)
                if is_rec_acceptor:
                    for idx in lig_donors:
                        dist = float(np.linalg.norm(lig_xyz[idx] - rec_xyz))
                        if dist > self.hbond_max_dist:
                            continue
                        atom = mol.GetAtomWithIdx(idx)
                        h_neighbors = [
                            nbr.GetIdx() for nbr in atom.GetNeighbors() if nbr.GetAtomicNum() == 1
                        ]
                        ang: float | None = None
                        if h_neighbors:
                            best_ang = max(
                                _angle_deg(lig_xyz[idx], lig_xyz[h_i], rec_xyz)
                                for h_i in h_neighbors
                            )
                            if best_ang < self.hbond_min_angle_deg:
                                continue
                            ang = round(best_ang, 1)
                        _record(
                            {
                                "type": "H-Bond",
                                "residue": res_label,
                                "chain": chain,
                                "atom_label": aname,
                                "lig_atom_label": f"{atom.GetSymbol()}{idx + 1}",
                                "distance_a": round(dist, 2),
                                "angle_deg": ang,
                                "lig_coords": _round_coords(lig_xyz[idx]),
                                "rec_coords": _round_coords(rec_xyz),
                            }
                        )

                # H-Bonds (Receptor Donor -> Ligand Acceptor)
                if is_rec_donor:
                    for idx in lig_acceptors:
                        dist = float(np.linalg.norm(lig_xyz[idx] - rec_xyz))
                        if dist <= self.hbond_max_dist:
                            atom = mol.GetAtomWithIdx(idx)
                            heavy_nbrs = [
                                nbr.GetIdx()
                                for nbr in atom.GetNeighbors()
                                if nbr.GetAtomicNum() > 1
                            ]
                            ang = (
                                round(
                                    max(
                                        _angle_deg(lig_xyz[n_i], lig_xyz[idx], rec_xyz)
                                        for n_i in heavy_nbrs
                                    ),
                                    1,
                                )
                                if heavy_nbrs
                                else None
                            )
                            if ang is not None and ang < 85.0:
                                continue
                            _record(
                                {
                                    "type": "H-Bond",
                                    "residue": res_label,
                                    "chain": chain,
                                    "atom_label": aname,
                                    "lig_atom_label": f"{atom.GetSymbol()}{idx + 1}",
                                    "distance_a": round(dist, 2),
                                    "angle_deg": ang,
                                    "lig_coords": _round_coords(lig_xyz[idx]),
                                    "rec_coords": _round_coords(rec_xyz),
                                }
                            )

                # Halogen Bonds (C-X...A for X in Cl, Br, I; NOT F)
                if elem in ("O", "N", "S"):
                    for atom in mol.GetAtoms():
                        sym = atom.GetSymbol().upper()
                        if sym not in ("CL", "BR", "I"):
                            continue
                        x_idx = atom.GetIdx()
                        dist = float(np.linalg.norm(lig_xyz[x_idx] - rec_xyz))
                        if dist > self.halogen_max_dist:
                            continue
                        c_nbrs = [
                            nbr.GetIdx()
                            for nbr in atom.GetNeighbors()
                            if nbr.GetSymbol() == "C"
                        ]
                        if not c_nbrs:
                            continue
                        sigma_angle = max(
                            _angle_deg(lig_xyz[c_i], lig_xyz[x_idx], rec_xyz)
                            for c_i in c_nbrs
                        )
                        if sigma_angle >= self.halogen_min_angle_deg:
                            _record(
                                {
                                    "type": "Halogen Bond",
                                    "residue": res_label,
                                    "chain": chain,
                                    "atom_label": aname,
                                    "lig_atom_label": f"{sym}{x_idx + 1}",
                                    "distance_a": round(dist, 2),
                                    "angle_deg": round(sigma_angle, 1),
                                    "lig_coords": _round_coords(lig_xyz[x_idx]),
                                    "rec_coords": _round_coords(rec_xyz),
                                }
                            )

                # Hydrophobic Contacts
                if is_rec_hydrophobic:
                    for idx in lig_hydrophobes:
                        dist = float(np.linalg.norm(lig_xyz[idx] - rec_xyz))
                        if dist <= self.hydrophobic_max_dist:
                            _record(
                                {
                                    "type": "Hydrophobic",
                                    "residue": res_label,
                                    "chain": chain,
                                    "atom_label": aname,
                                    "lig_atom_label": f"C{idx + 1}",
                                    "distance_a": round(dist, 2),
                                    "angle_deg": None,
                                    "lig_coords": _round_coords(lig_xyz[idx]),
                                    "rec_coords": _round_coords(rec_xyz),
                                }
                            )

        ordered = sorted(contacts_by_key.values(), key=lambda c: c["distance_a"])
        return ordered[:max_contacts]
