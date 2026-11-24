"""
Agentic BioNeMo - Retrosynthesis & Reaction Planner Agent (Dr. Chen)
Deconstructs lead candidate molecules via RDKit BRICS bond-cleavage fragmentation
into retrosynthetic synthons and proposes heuristic organic synthesis transformations.
"""

from __future__ import annotations

import re

from rdkit import Chem
from rdkit.Chem import BRICS

from bionemo_benchmark.core.models import MoleculeCandidate, RetrosynthesisPlan, RetrosynthesisStep


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
        )
