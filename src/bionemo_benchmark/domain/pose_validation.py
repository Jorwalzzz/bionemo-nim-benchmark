"""
3D Ligand Pose Plausibility Validator (Bond Geometry, Clashes, SVD Planarity, ΔE_strain).
Copyright (C) 2026 Jorwalzzz. Licensed under AGPL-3.0-only.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

from bionemo_benchmark.domain.pdb_utils import parse_pdb_heavy_atoms

# Bondi / Alvarez van der Waals radii (Angstroms)
_VDW_RADII: dict[str, float] = {
    "H": 1.20,
    "C": 1.70,
    "N": 1.55,
    "O": 1.52,
    "S": 1.80,
    "P": 1.80,
    "F": 1.47,
    "CL": 1.75,
    "BR": 1.85,
    "I": 1.98,
    "SE": 1.90,
}

# Single-bond covalent radii (Angstroms) for bond length sanity bounds
_COV_RADII: dict[str, float] = {
    "H": 0.31,
    "C": 0.76,
    "N": 0.71,
    "O": 0.66,
    "S": 1.05,
    "P": 1.07,
    "F": 0.57,
    "CL": 1.02,
    "BR": 1.20,
    "I": 1.39,
    "SE": 1.20,
}


def _finite_or_none(value: float | None, decimals: int = 3) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), decimals)


def _extract_covalent_target(covalent_residue: str | None) -> tuple[str, str] | None:
    if not covalent_residue:
        return None
    clean = covalent_residue.strip().upper()
    letters = "".join(ch for ch in clean if ch.isalpha())
    digits = "".join(ch for ch in clean if ch.isdigit())
    if not digits:
        return None
    return (letters[:3], digits)


class PosePlausibilityValidator:
    """Evaluates physical 3D plausibility of docked ligand SDF poses against receptor PDBs."""

    def __init__(
        self,
        max_planarity_dev_a: float = 0.15,
        max_strain_kcal_mol: float = 15.0,
        clash_vdw_scale: float = 0.70,
        covalent_cutoff_a: float = 2.20,
    ):
        self.max_planarity_dev_a = max_planarity_dev_a
        self.max_strain_kcal_mol = max_strain_kcal_mol
        self.clash_vdw_scale = clash_vdw_scale
        self.covalent_cutoff_a = covalent_cutoff_a

    @staticmethod
    def _compute_planarity_deviation(mol: Chem.Mol) -> tuple[bool, float]:
        if mol.GetNumConformers() == 0:
            return False, 99.0
        conf = mol.GetConformer()
        planar_groups: list[list[int]] = []

        # 5- and 6-membered aromatic rings
        for ring in mol.GetRingInfo().AtomRings():
            if len(ring) in (5, 6) and all(
                mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring
            ):
                planar_groups.append(list(ring))

        # Connected sp2 alkene groups (C=C + direct heavy substituents, up to 6 atoms)
        for bond in mol.GetBonds():
            if bond.GetBondType() == Chem.BondType.DOUBLE and not bond.GetIsAromatic():
                a1 = bond.GetBeginAtom()
                a2 = bond.GetEndAtom()
                if a1.GetSymbol() == "C" and a2.GetSymbol() == "C":
                    group = {a1.GetIdx(), a2.GetIdx()}
                    for nbr in a1.GetNeighbors():
                        if nbr.GetAtomicNum() > 1:
                            group.add(nbr.GetIdx())
                    for nbr in a2.GetNeighbors():
                        if nbr.GetAtomicNum() > 1:
                            group.add(nbr.GetIdx())
                    if len(group) >= 4:
                        planar_groups.append(sorted(group))

        if not planar_groups:
            return True, 0.0

        max_dev = 0.0
        for group in planar_groups:
            pts = np.array(
                [
                    [
                        conf.GetAtomPosition(i).x,
                        conf.GetAtomPosition(i).y,
                        conf.GetAtomPosition(i).z,
                    ]
                    for i in group
                ],
                dtype=float,
            )
            if pts.shape[0] < 4:
                continue
            centered = pts - pts.mean(axis=0)
            _, _, vt = np.linalg.svd(centered, full_matrices=False)
            normal = vt[-1]
            deviations = np.abs(centered @ normal)
            group_max = float(np.max(deviations))
            if group_max > max_dev:
                max_dev = group_max

        return max_dev <= 0.15, round(max_dev, 4)

    @staticmethod
    def _compute_strain_energy(mol: Chem.Mol) -> float | None:
        try:
            pose_mol = Chem.Mol(mol)
            if not any(a.GetAtomicNum() == 1 for a in pose_mol.GetAtoms()):
                pose_mol = Chem.AddHs(pose_mol, addCoords=True)
            props = AllChem.MMFFGetMoleculeProperties(pose_mol)
            if props is None:
                return None
            ff_pose = AllChem.MMFFGetMoleculeForceField(pose_mol, props)
            if ff_pose is None:
                return None
            # Freeze all heavy atoms while relaxing hydrogens to match ETKDG/MMFF parameterization
            for atom in pose_mol.GetAtoms():
                if atom.GetAtomicNum() > 1:
                    ff_pose.MMFFAddPositionConstraint(atom.GetIdx(), 0.0, 1000.0)
            ff_pose.Minimize(maxIts=50)
            e_pose = float(ff_pose.CalcEnergy())
            if not math.isfinite(e_pose):
                return None

            ref_smiles = Chem.MolToSmiles(Chem.RemoveHs(Chem.Mol(mol)))
            ref_mol = Chem.MolFromSmiles(ref_smiles)
            if ref_mol is None:
                return None
            ref_mol = Chem.AddHs(ref_mol)
            params = AllChem.ETKDGv3()
            params.randomSeed = 42
            conf_ids = AllChem.EmbedMultipleConfs(ref_mol, numConfs=5, params=params)
            if not conf_ids:
                return None
            res = AllChem.MMFFOptimizeMoleculeConfs(ref_mol, maxIters=200)
            valid_energies = [
                float(e) for _conv, e in res if e is not None and math.isfinite(float(e))
            ]
            if not valid_energies:
                return None
            delta_e = max(0.0, e_pose - min(valid_energies))
            return _finite_or_none(delta_e, 2)
        except Exception:
            return None

    def validate_pose(
        self,
        pose_sdf: str,
        pdb_text: str = "",
        covalent_residue: str | None = None,
    ) -> dict[str, Any]:
        """Runs comprehensive 3D pose plausibility checks and returns finite JSON metrics."""
        if not pose_sdf or not pose_sdf.strip():
            return {
                "passes_all": False,
                "bond_geometry_pass": False,
                "intra_clash_pass": False,
                "receptor_clash_pass": False,
                "planarity_pass": False,
                "strain_pass": True,
                "bad_bond_count": 0,
                "intra_clash_count": 0,
                "receptor_clash_count": 0,
                "covalent_proximity": False,
                "covalent_contacts": [],
                "max_planarity_dev_a": None,
                "strain_energy_kcal_mol": None,
                "error": "Empty SDF pose block.",
            }

        mol = Chem.MolFromMolBlock(pose_sdf, removeHs=False, sanitize=True)
        if mol is None or mol.GetNumConformers() == 0 or mol.GetNumAtoms() == 0:
            return {
                "passes_all": False,
                "bond_geometry_pass": False,
                "intra_clash_pass": False,
                "receptor_clash_pass": False,
                "planarity_pass": False,
                "strain_pass": True,
                "bad_bond_count": 0,
                "intra_clash_count": 0,
                "receptor_clash_count": 0,
                "covalent_proximity": False,
                "covalent_contacts": [],
                "max_planarity_dev_a": None,
                "strain_energy_kcal_mol": None,
                "error": "Unable to parse valid 3D ligand coordinates.",
            }

        conf = mol.GetConformer()
        n_atoms = mol.GetNumAtoms()
        coords = np.array(
            [
                [
                    conf.GetAtomPosition(i).x,
                    conf.GetAtomPosition(i).y,
                    conf.GetAtomPosition(i).z,
                ]
                for i in range(n_atoms)
            ],
            dtype=float,
        )
        elements = [mol.GetAtomWithIdx(i).GetSymbol().upper() for i in range(n_atoms)]
        atomic_nums = [mol.GetAtomWithIdx(i).GetAtomicNum() for i in range(n_atoms)]

        # 1. Covalent bond geometry checks
        bad_bond_count = 0
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            dist = float(np.linalg.norm(coords[i] - coords[j]))
            expected = _COV_RADII.get(elements[i], 0.77) + _COV_RADII.get(elements[j], 0.77)
            if dist < 0.62 * expected or dist > 1.42 * expected:
                bad_bond_count += 1
        bond_geometry_pass = bad_bond_count == 0

        # 2. Intramolecular steric clashes for heavy pairs separated by >= 4 bonds
        dist_mat = Chem.GetDistanceMatrix(mol)
        intra_clash_count = 0
        for i in range(n_atoms):
            if atomic_nums[i] <= 1:
                continue
            r_i = _VDW_RADII.get(elements[i], 1.70)
            for j in range(i + 1, n_atoms):
                if atomic_nums[j] <= 1 or dist_mat[i, j] < 4:
                    continue
                r_j = _VDW_RADII.get(elements[j], 1.70)
                dist = float(np.linalg.norm(coords[i] - coords[j]))
                if dist < self.clash_vdw_scale * (r_i + r_j):
                    intra_clash_count += 1
        intra_clash_pass = intra_clash_count == 0

        # 3. Receptor steric clashes (MODEL 1 / ATOM / altLoc in (' ', 'A') / heavy only)
        receptor_clash_count = 0
        covalent_proximity = False
        covalent_contacts: list[str] = []
        cov_target = _extract_covalent_target(covalent_residue)

        if pdb_text and pdb_text.strip():
            rec_atoms = parse_pdb_heavy_atoms(pdb_text)
            heavy_indices = [i for i in range(n_atoms) if atomic_nums[i] > 1]
            if rec_atoms and heavy_indices:
                lig_heavy = coords[heavy_indices]
                lig_vdw = np.array(
                    [_VDW_RADII.get(elements[i], 1.70) for i in heavy_indices], dtype=float
                )
                rec_coords = np.array(
                    [[a["x"], a["y"], a["z"]] for a in rec_atoms], dtype=float
                )
                rec_vdw = np.array(
                    [_VDW_RADII.get(a["element"], 1.70) for a in rec_atoms], dtype=float
                )
                # Pairwise distance matrix (N_lig, N_rec)
                diff = lig_heavy[:, None, :] - rec_coords[None, :, :]
                dists = np.linalg.norm(diff, axis=-1)
                min_allowed = self.clash_vdw_scale * (lig_vdw[:, None] + rec_vdw[None, :])
                clash_lig_idx, clash_rec_idx = np.where(dists < min_allowed)

                seen_rec_clashes: set[int] = set()
                for _li, ri in zip(clash_lig_idx, clash_rec_idx, strict=True):
                    ri_int = int(ri)
                    dist_val = float(dists[_li, ri_int])
                    atom_info = rec_atoms[ri_int]
                    matches_cov = False
                    if cov_target is not None:
                        cov_resname, cov_resnum = cov_target
                        if atom_info["resnum"] == cov_resnum and (
                            not cov_resname or atom_info["resname"].startswith(cov_resname)
                        ):
                            matches_cov = True
                    if matches_cov and dist_val <= self.covalent_cutoff_a:
                        covalent_proximity = True
                        label = f"{atom_info['resname'].capitalize()}{atom_info['resnum']}:{atom_info['atom_name']}"
                        if label not in covalent_contacts:
                            covalent_contacts.append(label)
                    elif ri_int not in seen_rec_clashes:
                        seen_rec_clashes.add(ri_int)
                        receptor_clash_count += 1

        receptor_clash_pass = receptor_clash_count == 0

        # 4. Aromatic/alkene planarity check via SVD
        planarity_ok, max_dev = self._compute_planarity_deviation(mol)
        planarity_pass = planarity_ok and (max_dev <= self.max_planarity_dev_a)

        # 5. Conformational strain ΔE_strain (kcal/mol)
        strain_kcal = self._compute_strain_energy(mol)
        strain_pass = strain_kcal is None or strain_kcal <= self.max_strain_kcal_mol

        passes_all = (
            bond_geometry_pass
            and intra_clash_pass
            and receptor_clash_pass
            and planarity_pass
            and strain_pass
        )

        return {
            "passes_all": passes_all,
            "bond_geometry_pass": bond_geometry_pass,
            "intra_clash_pass": intra_clash_pass,
            "receptor_clash_pass": receptor_clash_pass,
            "planarity_pass": planarity_pass,
            "strain_pass": strain_pass,
            "bad_bond_count": bad_bond_count,
            "intra_clash_count": intra_clash_count,
            "receptor_clash_count": receptor_clash_count,
            "covalent_proximity": covalent_proximity,
            "covalent_contacts": covalent_contacts,
            "max_planarity_dev_a": _finite_or_none(max_dev, 4),
            "strain_energy_kcal_mol": strain_kcal,
        }
