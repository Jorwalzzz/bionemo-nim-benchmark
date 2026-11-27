"""
TDD verification tests for Task 1: RDKit PAINS A/B/C + BRENK catalogs,
runtime Ertl SA Score, Daina & Zoete (2016) BOILED-Egg GI/BBB boundaries,
and multi-fragment salt handling.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

from bionemo_benchmark.agents.admet_critic import ADMETCriticAgent
from bionemo_benchmark.core.models import MoleculeCandidate


def test_pains_brenk_ertl_sa_and_salt_desalting() -> None:
    critic = ADMETCriticAgent()
    cands = [
        # Rhodanine core -> PAINS alert -> REJECT
        MoleculeCandidate(id="PAINS-1", smiles="O=C1NC(=S)SC1=Cc1ccccc1", parent_smiles="C"),
        # Nitrofuran -> BRENK alert -> FLAGGED/REJECT
        MoleculeCandidate(id="BRENK-1", smiles="O=[N+]([O-])c1ccco1", parent_smiles="C"),
        # Acetate sodium salt -> desalt via LargestFragmentChooser, flag is_salt_desalted=True
        MoleculeCandidate(id="SALT-1", smiles="CC(=O)O.[Na+]", parent_smiles="C"),
        # Clean drug control -> PASS with valid Ertl SA bounds
        MoleculeCandidate(id="SAFE-1", smiles="COc1ccc(CCNC(=O)c2ccncc2)cc1", parent_smiles="C"),
    ]
    evaluated, _ = critic.evaluate_candidates(cands)

    assert evaluated[0].admet_verdict == "REJECT"
    assert len(evaluated[0].pains_alerts) >= 1

    assert len(evaluated[1].brenk_alerts) >= 1
    assert evaluated[1].admet_verdict in ("FLAGGED", "REJECT")

    assert evaluated[2].is_salt_desalted is True
    assert evaluated[2].admet_verdict in ("PASS", "FLAGGED")

    assert evaluated[3].is_salt_desalted is False
    assert evaluated[3].admet_verdict == "PASS"
    assert 1.0 <= evaluated[3].sascore <= 10.0


def test_boiled_egg_gi_and_bbb_classification() -> None:
    critic = ADMETCriticAgent()
    cands = [
        # Diazepam (lipophilic CNS drug, low TPSA ~32.7, WLOGP ~3.1) -> GI High + BBB Permeable
        MoleculeCandidate(id="CNS-DIAZ", smiles="CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21", parent_smiles="C"),
        # Atenolol (polar peripheral beta-blocker, high TPSA ~84.6, low WLOGP ~0.35) -> GI High, NOT BBB
        MoleculeCandidate(id="GI-ATEN", smiles="CC(C)NCC(O)COc1ccc(CC(N)=O)cc1", parent_smiles="C"),
        # Vancomycin-like high-TPSA polar peptide mimic -> GI Low, NOT BBB
        MoleculeCandidate(id="LOW-POLAR", smiles="O=C(O)C(N)CC(=O)NC(CC(=O)O)C(=O)NC(CC(=O)O)C(=O)O", parent_smiles="C"),
    ]
    evaluated, _ = critic.evaluate_candidates(cands)

    diaz, aten, polar = evaluated
    assert diaz.gi_absorption_high is True and diaz.bbb_permeable is True
    assert aten.gi_absorption_high is True and aten.bbb_permeable is False
    assert polar.gi_absorption_high is False and polar.bbb_permeable is False
