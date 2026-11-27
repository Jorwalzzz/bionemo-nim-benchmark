"""
Agentic BioNeMo - Retrosynthesis & Reaction Planner Agent (Dr. Chen)
Deconstructs lead candidate molecules via RDKit BRICS bond-cleavage fragmentation
into retrosynthetic synthons and proposes heuristic organic synthesis transformations.
"""

from __future__ import annotations

import re
from typing import Any

from rdkit import Chem
from rdkit.Chem import BRICS

from bionemo_benchmark.core.models import MoleculeCandidate, RetrosynthesisPlan, RetrosynthesisStep

_DUMMY_QUERY = Chem.MolFromSmarts("[#0]")
_HYDROGEN_REP = Chem.MolFromSmiles("[H]")


class RetrosynthesisAgent:
    def __init__(self):
        self.agent_id = "retro"
        self.persona_name = "Dr. Chen (Retrosynthesis Planner)"
        self.avatar = "🔬"

    @staticmethod
    def _extract_brics_precursors(mol: Chem.Mol, fallback_smiles: str) -> tuple[list[dict[str, str]], list[str]]:
        """Decompose molecule via RDKit BRICS into actual candidate-specific synthon fragments."""
        raw_fragments = sorted(BRICS.BRICSDecompose(mol, minFragmentSize=3))
        if not raw_fragments:
            raw_fragments = [Chem.MolToSmiles(mol, isomericSmiles=True) or fallback_smiles]

        reactants: list[dict[str, str]] = []
        materials: list[str] = []
        for idx, brics_smi in enumerate(raw_fragments[:4], start=1):
            clean_smi = re.sub(r"\[\d+\*\]", "[*]", brics_smi)
            label = f"BRICS Synthon {idx}"
            reactants.append(
                {
                    "name": label,
                    "smiles": clean_smi,
                    "source": "BRICS Retrosynthetic Disconnection (In Silico Fragmentation)",
                }
            )
            materials.append(f"BRICS Synthon {idx}: {clean_smi}")
        return reactants, materials

    @staticmethod
    def _cap_dummy_atoms(frag_mol: Chem.Mol) -> Chem.Mol | None:
        """Replaces BRICS dummy [*] attachment atoms cleanly with hydrogens and sanitizes."""
        try:
            copy_mol = Chem.Mol(frag_mol)
            Chem.SanitizeMol(copy_mol, catchErrors=True)
            if _DUMMY_QUERY is not None and _HYDROGEN_REP is not None:
                replaced = Chem.ReplaceSubstructs(
                    copy_mol, _DUMMY_QUERY, _HYDROGEN_REP, replaceAll=True
                )
                if replaced:
                    copy_mol = replaced[0]
            clean_mol = Chem.RemoveHs(copy_mol)
            Chem.SanitizeMol(clean_mol)
            return clean_mol
        except Exception:
            try:
                smi = re.sub(r"\[\d*\*\]|\*", "", Chem.MolToSmiles(frag_mol))
                fallback = Chem.MolFromSmiles(smi)
                if fallback is not None:
                    Chem.SanitizeMol(fallback)
                return fallback
            except Exception:
                return None

    @staticmethod
    def _classify_brics_reaction(
        mol: Chem.Mol, u: int, v: int, lbl_u: str, lbl_v: str
    ) -> tuple[str, list[str]]:
        a_u = mol.GetAtomWithIdx(u)
        a_v = mol.GetAtomWithIdx(v)
        syms = {a_u.GetSymbol(), a_v.GetSymbol()}
        is_arom_pair = a_u.GetIsAromatic() and a_v.GetIsAromatic()

        def _has_carbonyl_o(atom: Chem.Atom) -> bool:
            return atom.GetSymbol() == "C" and any(
                b.GetBondType() == Chem.BondType.DOUBLE
                and b.GetOtherAtom(atom).GetSymbol() == "O"
                for b in atom.GetBonds()
            )

        if syms == {"C", "N"} and (_has_carbonyl_o(a_u) or _has_carbonyl_o(a_v)):
            return (
                "Amide Coupling (HATU / DIPEA)",
                ["HATU (1.2 equiv)", "DIPEA (2.5 equiv), DMF, 25°C"],
            )
        if syms == {"C", "O"} and (_has_carbonyl_o(a_u) or _has_carbonyl_o(a_v)):
            return (
                "Esterification / Acylation",
                ["EDCI (1.2 equiv)", "DMAP (0.1 equiv), DCM"],
            )
        if is_arom_pair and syms == {"C"}:
            return (
                "Suzuki-Miyaura Cross-Coupling",
                ["Pd(dppf)Cl2 (5 mol%)", "K2CO3, Dioxane/H2O, 90°C"],
            )
        if syms == {"C", "N"} and (a_u.GetIsAromatic() or a_v.GetIsAromatic()):
            return (
                "Buchwald-Hartwig / SNAr Amination",
                ["Pd2(dba)3 / XPhos", "Cs2CO3, Toluene, 100°C"],
            )
        if "O" in syms:
            return (
                "Williamson Ether / Mitsunobu Coupling",
                ["K2CO3, DMF, 60°C"],
            )
        return (
            f"BRICS Fragment Coupling ({lbl_u}-{lbl_v})",
            ["Heuristic Catalyst / Base System"],
        )

    def _split_single_best_brics_bond(
        self, mol: Chem.Mol
    ) -> tuple[str, list[str], tuple[Chem.Mol, Chem.Mol]] | None:
        """Finds the single most mass-balanced cleavable BRICS bond giving 2 valid fragments."""
        try:
            brics_bonds = list(BRICS.FindBRICSBonds(mol))
        except Exception:
            return None
        if not brics_bonds:
            return None

        best_score: tuple[int, int] | None = None
        best_result: tuple[str, list[str], tuple[Chem.Mol, Chem.Mol]] | None = None

        for (u, v), (lbl_u, lbl_v) in brics_bonds:
            bond = mol.GetBondBetweenAtoms(u, v)
            if bond is None:
                continue
            try:
                frag_mol = Chem.FragmentOnBonds(mol, [bond.GetIdx()], addDummies=True)
                parts = Chem.GetMolFrags(frag_mol, asMols=True, sanitizeFrags=False)
            except Exception:
                continue
            if len(parts) != 2:
                continue
            cap_a = self._cap_dummy_atoms(parts[0])
            cap_b = self._cap_dummy_atoms(parts[1])
            if cap_a is None or cap_b is None:
                continue
            n_a = cap_a.GetNumHeavyAtoms()
            n_b = cap_b.GetNumHeavyAtoms()
            if n_a < 3 or n_b < 3:
                continue
            score = (abs(n_a - n_b), -(n_a + n_b))
            if best_score is None or score < best_score:
                best_score = score
                rxn_type, reagents = self._classify_brics_reaction(mol, u, v, lbl_u, lbl_v)
                best_result = (rxn_type, reagents, (cap_a, cap_b))

        return best_result

    def _build_brics_tree(
        self, mol: Chem.Mol, depth: int = 0, max_depth: int = 3
    ) -> dict[str, Any]:
        """Builds a bounded depth-3 recursive binary retrosynthetic tree cleanly."""
        clean_smi = Chem.MolToSmiles(mol, isomericSmiles=True)
        if "*" in clean_smi:
            clean_smi = clean_smi.replace("*", "")

        if depth >= max_depth or mol.GetNumHeavyAtoms() < 7:
            return {
                "smiles": clean_smi,
                "depth": depth,
                "reaction_type": "Terminal Building Block",
                "reagents": [],
                "status": "Heuristic Terminal Fragment",
                "children": [],
            }

        split = self._split_single_best_brics_bond(mol)
        if split is None:
            return {
                "smiles": clean_smi,
                "depth": depth,
                "reaction_type": "Terminal Building Block",
                "reagents": [],
                "status": "Heuristic Terminal Fragment",
                "children": [],
            }

        rxn_type, reagents, (cap_a, cap_b) = split
        child_a = self._build_brics_tree(cap_a, depth=depth + 1, max_depth=max_depth)
        child_b = self._build_brics_tree(cap_b, depth=depth + 1, max_depth=max_depth)
        return {
            "smiles": clean_smi,
            "depth": depth,
            "reaction_type": rxn_type,
            "reagents": reagents,
            "status": "Disconnection Step",
            "children": [child_a, child_b],
        }

    def plan_synthesis_route(self, candidate: MoleculeCandidate) -> RetrosynthesisPlan:
        """Analyze candidate topology via RDKit BRICS and propose retrosynthetic disconnections."""
        mol = Chem.MolFromSmiles(candidate.smiles)
        if not mol:
            return RetrosynthesisPlan(
                candidate_id=candidate.id,
                target_smiles=candidate.smiles,
                num_steps=0,
                overall_feasibility="Invalid SMILES structure",
                steps=[],
            )

        brics_reactants, brics_materials = self._extract_brics_precursors(mol, candidate.smiles)
        steps: list[RetrosynthesisStep] = []
        starting_materials: list[str] = list(brics_materials)

        has_amide = mol.HasSubstructMatch(Chem.MolFromSmarts("[NX3][CX3](=[OX1])"))
        has_biaryl = mol.HasSubstructMatch(Chem.MolFromSmarts("[c:1]-[c:2]"))
        has_aromatic_amine = mol.HasSubstructMatch(Chem.MolFromSmarts("[c:1][NX3]"))

        step_counter = 1
        primary_pair = brics_reactants[:2] if len(brics_reactants) >= 2 else brics_reactants

        if has_amide:
            steps.append(
                RetrosynthesisStep(
                    step_number=step_counter,
                    reaction_type="BRICS Retrosynthetic Disconnections — Amide Coupling",
                    reaction_smarts="[C:1](=O)[OH] + [N:2][H] >> [C:1](=O)[N:2]",
                    reactants=primary_pair,
                    reagents=[
                        "Heuristic Reagent Recommendation: HATU (1.2 equiv)",
                        "Heuristic Reagent Recommendation: DIPEA (2.5 equiv), DMF, 25°C",
                    ],
                    product_smiles=candidate.smiles,
                    estimated_yield_pct=84.5,
                    difficulty="Routine (Heuristic)",
                )
            )
            step_counter += 1

        if has_biaryl:
            biaryl_pair = brics_reactants[1:3] if len(brics_reactants) >= 3 else primary_pair
            steps.append(
                RetrosynthesisStep(
                    step_number=step_counter,
                    reaction_type="BRICS Retrosynthetic Disconnections — Suzuki-Miyaura Coupling",
                    reaction_smarts="[c:1]-[X] + [c:2]-B(OH)2 >> [c:1]-[c:2]",
                    reactants=biaryl_pair,
                    reagents=[
                        "Heuristic Reagent Recommendation: Pd(dppf)Cl2 (5 mol%)",
                        "Heuristic Reagent Recommendation: K2CO3, 1,4-Dioxane:H2O, 90°C",
                    ],
                    product_smiles=candidate.smiles,
                    estimated_yield_pct=76.0,
                    difficulty="Moderate (Heuristic)",
                )
            )
            step_counter += 1

        elif has_aromatic_amine and not steps:
            steps.append(
                RetrosynthesisStep(
                    step_number=step_counter,
                    reaction_type="BRICS Retrosynthetic Disconnections — SNAr C-N Coupling",
                    reaction_smarts="[c:1][Cl] + [N:2] >> [c:1][N:2]",
                    reactants=primary_pair,
                    reagents=[
                        "Heuristic Reagent Recommendation: i-PrOH, catalytic acid or base",
                    ],
                    product_smiles=candidate.smiles,
                    estimated_yield_pct=81.0,
                    difficulty="Routine (Heuristic)",
                )
            )
            step_counter += 1

        if not steps:
            steps.append(
                RetrosynthesisStep(
                    step_number=1,
                    reaction_type="BRICS Retrosynthetic Disconnections — Late-Stage Fragment Assembly",
                    reaction_smarts="[N:1] + [C:2][Br] >> [N:1][C:2]",
                    reactants=primary_pair,
                    reagents=[
                        "Heuristic Reagent Recommendation: K2CO3 (2.5 equiv), MeCN",
                    ],
                    product_smiles=candidate.smiles,
                    estimated_yield_pct=72.0,
                    difficulty="Routine (Heuristic)",
                )
            )

        route_tree = self._build_brics_tree(mol, depth=0, max_depth=3)
        children = route_tree.get("children", [])
        is_convergent = len(children) == 2 and any(
            len(c.get("children", [])) == 2 for c in children
        )

        feasibility = (
            f"BRICS Retrosynthetic Disconnections ({len(steps)} bond-cleavage step(s), {len(brics_reactants)} synthons — Heuristic)"
        )
        turnaround = 5 if len(steps) == 1 else 10

        return RetrosynthesisPlan(
            candidate_id=candidate.id,
            target_smiles=candidate.smiles,
            num_steps=len(steps),
            overall_feasibility=feasibility,
            steps=steps,
            starting_materials=list(dict.fromkeys(starting_materials)),
            estimated_turnaround_days=turnaround,
            route_tree=route_tree,
            is_convergent=is_convergent,
        )
