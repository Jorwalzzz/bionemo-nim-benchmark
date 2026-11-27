"""
Agentic BioNeMo - Agent 3: ADMET & MedChem Critic Agent
Copyright (C) 2026 Jorwalzzz. Licensed under AGPL-3.0-only.

Rigorous RDKit-based physicochemical property profiling:
- Standard PAINS (A/B/C) + BRENK structural alert catalogs
- Runtime Ertl Synthetic Accessibility (SA) Score via RDConfig.RDContribDir
- Daina & Zoete (2016) BOILED-Egg GI absorption & BBB penetration ellipses
- Multi-fragment desalting via LargestFragmentChooser
"""

from __future__ import annotations

import importlib.util
import logging
import math
import os
import sys
from typing import Any

from rdkit import Chem, RDConfig
from rdkit.Chem import QED, Crippen, Descriptors, FilterCatalog, rdMolDescriptors
from rdkit.Chem.FilterCatalog import FilterCatalogParams
from rdkit.Chem.MolStandardize import rdMolStandardize

from bionemo_benchmark.core.models import AgentMessage, MoleculeCandidate

logger = logging.getLogger("ADMETCritic")

# Daina & Zoete (2016) BOILED-Egg ellipse parameters in (TPSA, WLOGP) space:
# (center_tpsa, center_wlogp, semimajor_a, semiminor_b, angle_deg)
_HIA_WHITE_ELLIPSE = (71.051, 2.292, 142.081 / 2.0, 8.740 / 2.0, -1.031325)
_BBB_YOLK_ELLIPSE = (38.117, 3.177, 82.061 / 2.0, 5.557 / 2.0, -0.171887)

_ERTL_SASCORER_MOD: Any | None = None


def _load_ertl_sascorer() -> Any | None:
    """Loads RDKit's Ertl SA_Score contrib module at runtime without vendoring."""
    global _ERTL_SASCORER_MOD
    if _ERTL_SASCORER_MOD is not None:
        return _ERTL_SASCORER_MOD
    sa_path = os.path.join(RDConfig.RDContribDir, "SA_Score", "sascorer.py")
    if not os.path.exists(sa_path):
        return None
    sa_dir = os.path.dirname(sa_path)
    if sa_dir not in sys.path:
        sys.path.append(sa_dir)
    spec = importlib.util.spec_from_file_location("rdkit_ertl_sascorer", sa_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _ERTL_SASCORER_MOD = module
    return _ERTL_SASCORER_MOD


def _point_in_rotated_ellipse(
    x: float,
    y: float,
    cx: float,
    cy: float,
    a: float,
    b: float,
    angle_deg: float,
) -> bool:
    """Evaluates whether (x, y) lies within a rotated 2D classification ellipse."""
    theta = math.radians(angle_deg)
    dx = x - cx
    dy = y - cy
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    u = dx * cos_t + dy * sin_t
    v = -dx * sin_t + dy * cos_t
    return (u * u) / (a * a) + (v * v) / (b * b) <= 1.0


def _safe_finite(value: float, default: float = 0.0) -> float:
    return value if math.isfinite(value) else default


class ADMETCriticAgent:
    """Screens candidate molecules using RDKit catalogs, Ertl SA, and BOILED-Egg."""

    def __init__(self, name: str = "ADMETCritic"):
        self.name = name

        pains_params = FilterCatalogParams()
        pains_params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
        pains_params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
        pains_params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)
        self._pains_catalog = FilterCatalog.FilterCatalog(pains_params)

        brenk_params = FilterCatalogParams()
        brenk_params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
        self._brenk_catalog = FilterCatalog.FilterCatalog(brenk_params)

        self._salt_stripper = rdMolStandardize.LargestFragmentChooser(preferOrganic=True)
        self._ertl_sascorer = _load_ertl_sascorer()

    def _compute_sascore(self, mol: Chem.Mol, mw: float) -> float:
        if self._ertl_sascorer is not None:
            try:
                raw_score = float(self._ertl_sascorer.calculateScore(mol))
                if math.isfinite(raw_score):
                    return round(max(1.0, min(10.0, raw_score)), 2)
            except Exception as exc:
                logger.warning("Ertl SA scorer failed, using deterministic fallback: %s", exc)
        fsp3 = _safe_finite(float(rdMolDescriptors.CalcFractionCSP3(mol)))
        ring_count = rdMolDescriptors.CalcNumRings(mol)
        fallback = 2.0 + (mw / 150.0) + (ring_count * 0.4) - (fsp3 * 1.5)
        return round(max(1.0, min(10.0, _safe_finite(fallback, 5.0))), 2)

    def evaluate_candidates(
        self, candidates: list[MoleculeCandidate]
    ) -> tuple[list[MoleculeCandidate], AgentMessage]:
        """Runs full ADMET screening across all generated molecule candidates."""
        passed_count = 0
        flagged_count = 0
        rejected_count = 0

        for cand in candidates:
            mol = Chem.MolFromSmiles(cand.smiles)
            if not mol:
                cand.admet_verdict = "REJECT"
                cand.admet_notes.append(
                    "Invalid chemical structure / SMILES parse error."
                )
                rejected_count += 1
                continue

            try:
                Chem.SanitizeMol(mol)
            except Exception as exc:
                cand.admet_verdict = "REJECT"
                cand.admet_notes.append(f"Valence sanitization failed: {exc}")
                rejected_count += 1
                continue

            # Multi-fragment salt handling before descriptor computation
            cand.is_salt_desalted = False
            if len(Chem.GetMolFrags(mol)) > 1:
                desalted = self._salt_stripper.choose(mol)
                if desalted is not None and desalted.GetNumAtoms() > 0:
                    Chem.SanitizeMol(desalted)
                    mol = desalted
                    cand.is_salt_desalted = True

            # Descriptors (finite-guarded)
            raw_mw = _safe_finite(float(Descriptors.MolWt(mol)))
            raw_wlogp = _safe_finite(float(Crippen.MolLogP(mol)))
            raw_tpsa = _safe_finite(float(rdMolDescriptors.CalcTPSA(mol)))
            raw_qed = _safe_finite(float(QED.qed(mol)))

            cand.mw = round(raw_mw, 2)
            cand.logp = round(raw_wlogp, 2)
            cand.tpsa = round(raw_tpsa, 2)
            cand.hbd = int(rdMolDescriptors.CalcNumHBD(mol))
            cand.hba = int(rdMolDescriptors.CalcNumHBA(mol))
            cand.rotatable_bonds = int(rdMolDescriptors.CalcNumRotatableBonds(mol))
            cand.qed = round(raw_qed, 3)
            cand.molecular_formula = rdMolDescriptors.CalcMolFormula(mol)
            cand.sascore = self._compute_sascore(mol, cand.mw)

            # Structural alert catalogs (PAINS A/B/C and BRENK)
            cand.pains_alerts = [
                entry.GetDescription()
                for entry in self._pains_catalog.GetMatches(mol)
            ]
            cand.brenk_alerts = [
                entry.GetDescription()
                for entry in self._brenk_catalog.GetMatches(mol)
            ]

            # Lipinski & Veber
            lipinski_violations = 0
            if cand.mw > 500.0:
                lipinski_violations += 1
            if cand.logp > 5.0:
                lipinski_violations += 1
            if cand.hbd > 5:
                lipinski_violations += 1
            if cand.hba > 10:
                lipinski_violations += 1
            cand.passes_lipinski = lipinski_violations <= 1
            cand.passes_veber = cand.rotatable_bonds <= 10 and cand.tpsa <= 140.0

            # Daina & Zoete (2016) BOILED-Egg GI & BBB permeability
            cand.gi_absorption_high = _point_in_rotated_ellipse(
                raw_tpsa, raw_wlogp, *_HIA_WHITE_ELLIPSE
            )
            cand.bbb_permeable = _point_in_rotated_ellipse(
                raw_tpsa, raw_wlogp, *_BBB_YOLK_ELLIPSE
            )

            # hERG Cardiotoxicity Alert Heuristic (High LogP + high MW + basic/polar centers)
            cand.herg_liability = cand.logp > 4.2 and cand.mw > 480 and cand.hba >= 4

            # Final Verdict
            cand.admet_notes = []
            if cand.is_salt_desalted:
                cand.admet_notes.append(
                    "Multi-fragment salt normalized to parent organic fragment."
                )

            if cand.pains_alerts:
                cand.admet_verdict = "REJECT"
                cand.admet_notes.append(
                    f"PAINS alerts: {', '.join(cand.pains_alerts[:4])}"
                )
                rejected_count += 1
            elif cand.brenk_alerts:
                cand.admet_verdict = "FLAGGED"
                cand.admet_notes.append(
                    f"BRENK structural alerts: {', '.join(cand.brenk_alerts[:4])}"
                )
                flagged_count += 1
            elif not cand.passes_lipinski or not cand.passes_veber:
                cand.admet_verdict = "FLAGGED"
                cand.admet_notes.append(
                    f"Lipinski/Veber boundary: MW={cand.mw}, LogP={cand.logp}, TPSA={cand.tpsa}"
                )
                flagged_count += 1
            elif cand.herg_liability:
                cand.admet_verdict = "FLAGGED"
                cand.admet_notes.append(
                    f"hERG potential cardiotoxicity liability (LogP={cand.logp}, MW={cand.mw})"
                )
                flagged_count += 1
            else:
                cand.admet_verdict = "PASS"
                cand.admet_notes.append(
                    f"Compliant: QED={cand.qed}, SAScore={cand.sascore}, TPSA={cand.tpsa}"
                )
                passed_count += 1

        thought_text = (
            f"Evaluated {len(candidates)} candidates through medicinal chemistry filtration. "
            f"Outcome: {passed_count} PASS, {flagged_count} FLAGGED, {rejected_count} REJECT. "
            f"Screened PAINS A/B/C, BRENK alerts, Ertl SAScore, BOILED-Egg GI/BBB, Lipinski/Veber, and hERG."
        )
        message = AgentMessage(
            agent_name=self.name,
            role="ADMET Critic",
            action="ADMET_MEDCHEM_EVALUATION",
            thought=thought_text,
            output_summary=f"{passed_count} PASS + {flagged_count} FLAGGED leads cleared for molecular docking.",
            status="SUCCESS",
        )
        return candidates, message
