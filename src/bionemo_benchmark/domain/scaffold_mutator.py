"""
RDKit bioisosteric SMARTS & BRICS scaffold mutator.
Copyright (C) 2026 Jorwalzzz. Licensed under AGPL-3.0-only.
"""

from __future__ import annotations

import itertools
import random

from rdkit import Chem
from rdkit.Chem import BRICS, Descriptors, rdChemReactions

# Clean medicinal-chemistry bioisostere transforms authored directly in SMARTS
_BIOISOSTERE_SMARTS: tuple[str, ...] = (
    "[c:1][Cl]>>[c:1]F",
    "[c:1][Cl]>>[c:1]C(F)(F)F",
    "[c:1]F>>[c:1]Cl",
    "[c:1][cH:2][c:3]>>[c:1][n:2][c:3]",
    "[O:1][CH3]>>[O:1]CC",
    "[O:1][CH3]>>[O:1]C(F)F",
    "[c:1][NH2]>>[c:1]NC",
    "[C:1](=[O:2])[NH:3][C:4]>>[C:1](=[O:2])[N:3](C)[C:4]",
    "[C:1](=[O:2])[OH]>>[C:1]1=NN=NN1",
    "[c:1][CH3]>>[c:1]C1CC1",
    "[O:1]=[S:2](=[O:3])[NH:4]>>[O:1]=[S:2](=[O:3])[N:4]C",
    "[c:1]c2ccco2>>[c:1]c2cccs2",
    "[cH:1][c:2][C:3](=[O:4])>>[c:1](F)[c:2][C:3](=[O:4])",
)

_COMPILED_REACTIONS: list[rdChemReactions.ChemicalReaction] = [
    rxn
    for smarts in _BIOISOSTERE_SMARTS
    if (rxn := rdChemReactions.ReactionFromSmarts(smarts)) is not None
]


def _try_sanitize_canonical(mol: Chem.Mol, max_mw: float) -> str | None:
    try:
        copy_mol = Chem.Mol(mol)
        Chem.SanitizeMol(copy_mol)
        if Descriptors.MolWt(copy_mol) > max_mw:
            return None
        return Chem.MolToSmiles(copy_mol, isomericSmiles=True)
    except Exception:
        return None


def mutate_parent_scaffold(
    parent_smiles: str,
    seed: int = 42,
    max_variants: int = 12,
) -> list[str]:
    """
    Generates deterministic, RDKit-validated bioisostere & BRICS analogs
    from any valid parent scaffold SMILES (target-agnostic).
    """
    if max_variants <= 0:
        return []

    mol = Chem.MolFromSmiles(parent_smiles)
    if mol is None:
        return []
    try:
        Chem.SanitizeMol(mol)
    except Exception:
        return []

    parent_canon = Chem.MolToSmiles(mol, isomericSmiles=True)
    max_mw = max(750.0, float(Descriptors.MolWt(mol)) + 150.0)
    rng = random.Random(seed)

    seen: set[str] = {parent_canon}
    generated: list[str] = []

    def _collect_from_mol(source_mol: Chem.Mol) -> None:
        rxns = list(_COMPILED_REACTIONS)
        rng.shuffle(rxns)
        for rxn in rxns:
            try:
                products = rxn.RunReactants((source_mol,))
            except Exception:
                continue
            for prod_tuple in products:
                if not prod_tuple:
                    continue
                smi = _try_sanitize_canonical(prod_tuple[0], max_mw=max_mw)
                if smi and smi not in seen:
                    seen.add(smi)
                    generated.append(smi)
                    if len(generated) >= max_variants * 2:
                        return

    _collect_from_mol(mol)

    # Second-order mutations if first-order pool is still sparse
    if len(generated) < max_variants:
        for smi in list(generated[:4]):
            sub_mol = Chem.MolFromSmiles(smi)
            if sub_mol is not None:
                _collect_from_mol(sub_mol)
                if len(generated) >= max_variants * 2:
                    break

    # Capped BRICS recombination for structural diversity
    if len(generated) < max_variants:
        try:
            frags = BRICS.BRICSDecompose(mol, minFragmentSize=2)
            frag_mols = [Chem.MolFromSmiles(f) for f in sorted(frags) if Chem.MolFromSmiles(f)]
            if len(frag_mols) >= 2:
                builder = BRICS.BRICSBuild(frag_mols, onlyCompleteMols=True)
                for recombined in itertools.islice(builder, 32):
                    smi = _try_sanitize_canonical(recombined, max_mw=max_mw)
                    if smi and smi not in seen:
                        seen.add(smi)
                        generated.append(smi)
                        if len(generated) >= max_variants * 2:
                            break
        except Exception:
            pass

    if not generated:
        return [parent_canon]

    result = [parent_canon, *generated]
    return result[:max_variants]
