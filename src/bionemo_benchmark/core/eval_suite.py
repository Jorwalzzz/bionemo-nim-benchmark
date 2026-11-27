"""
Murcko-Scaffold Cluster-Stratified Evaluation Suite (Bootstrap CIs, RMSD<=2A, EF10%).
Copyright (C) 2026 Jorwalzzz. Licensed under AGPL-3.0-only.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold


@dataclass
class ScaffoldEvaluatedRecord:
    """Single ligand/complex record evaluated for pose accuracy & enrichment."""

    smiles: str
    rmsd: float | None = None
    is_active: bool = False
    score: float | None = None


def extract_murcko_scaffold(smiles: str) -> str:
    """Extracts Bemis-Murcko generic scaffold SMILES deterministically."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "INVALID_SMILES"
    try:
        scaf = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
        return scaf if scaf else "ACYCLIC"
    except Exception:
        return "ACYCLIC"


def bootstrap_cluster_ci(
    clusters: list[list[float]],
    seed: int = 42,
    n_boot: int = 1000,
) -> tuple[float | None, float | None]:
    """Computes cluster-bootstrap 95% confidence interval by resampling Murcko clusters."""
    non_empty = [c for c in clusters if c]
    n_clusters = len(non_empty)
    if n_clusters == 0 or n_boot <= 0:
        return None, None

    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_boot):
        sampled_vals: list[float] = []
        for _ in range(n_clusters):
            chosen = non_empty[rng.randrange(n_clusters)]
            sampled_vals.extend(chosen)
        if sampled_vals:
            val = float(sum(sampled_vals) / len(sampled_vals))
            if math.isfinite(val):
                boot_means.append(val)

    if not boot_means:
        return None, None
    low = float(np.percentile(boot_means, 2.5))
    high = float(np.percentile(boot_means, 97.5))
    if not (math.isfinite(low) and math.isfinite(high)):
        return None, None
    return round(low, 4), round(high, 4)


def compute_ef10(records: list[ScaffoldEvaluatedRecord]) -> float | None:
    """
    Computes Top-10% Enrichment Factor (EF10%) strictly requiring explicit numeric scores.
    Returns None when any record lacks a finite numeric score or baseline actives == 0.
    """
    if not records:
        return None
    if any(r.score is None or not math.isfinite(float(r.score)) for r in records):
        return None

    total = len(records)
    total_actives = sum(1 for r in records if r.is_active)
    if total_actives == 0:
        return None

    ranked = sorted(records, key=lambda r: float(r.score), reverse=True)  # type: ignore[arg-type]
    top_k = max(1, math.ceil(0.10 * total))
    top_hits = sum(1 for r in ranked[:top_k] if r.is_active)

    baseline_rate = total_actives / float(total)
    top_rate = top_hits / float(top_k)
    ef = top_rate / baseline_rate
    return round(ef, 3) if math.isfinite(ef) else None


def evaluate_benchmark_suite(
    records: list[ScaffoldEvaluatedRecord],
    seed: int = 42,
    n_boot: int = 1000,
) -> dict[str, Any]:
    """Computes scaffold-stratified RMSD <= 2.0A pass rate, cluster bootstrap CI95, and EF10%."""
    if not records:
        return {
            "num_records": 0,
            "num_scaffold_clusters": 0,
            "rmsd_2a_pass_rate": None,
            "rmsd_2a_ci95": [None, None],
            "ef10": None,
            "scaffold_cluster_sizes": {},
        }

    clusters_map: dict[str, list[float]] = defaultdict(list)
    rmsd_flags_all: list[float] = []
    cluster_sizes: dict[str, int] = defaultdict(int)

    for rec in records:
        scaf = extract_murcko_scaffold(rec.smiles)
        cluster_sizes[scaf] += 1
        if rec.rmsd is not None and math.isfinite(float(rec.rmsd)):
            flag = 1.0 if float(rec.rmsd) <= 2.0 else 0.0
            clusters_map[scaf].append(flag)
            rmsd_flags_all.append(flag)

    pass_rate: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    if rmsd_flags_all:
        raw_rate = sum(rmsd_flags_all) / float(len(rmsd_flags_all))
        pass_rate = round(raw_rate, 4) if math.isfinite(raw_rate) else None
        ci_low, ci_high = bootstrap_cluster_ci(
            list(clusters_map.values()), seed=seed, n_boot=n_boot
        )

    ef10 = compute_ef10(records)
    return {
        "num_records": len(records),
        "num_scaffold_clusters": len(cluster_sizes),
        "rmsd_2a_pass_rate": pass_rate,
        "rmsd_2a_ci95": [ci_low, ci_high],
        "ef10": ef10,
        "scaffold_cluster_sizes": dict(sorted(cluster_sizes.items())),
    }
