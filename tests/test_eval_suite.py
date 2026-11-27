"""
TDD verification tests for Task 6: Murcko-scaffold cluster-stratified evaluator & EF10%.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import math

from bionemo_benchmark.core.eval_suite import ScaffoldEvaluatedRecord, evaluate_benchmark_suite


def test_murcko_scaffold_cluster_bootstrap_and_rmsd_and_ef10() -> None:
    records = [
        # Cluster 1: Benzene scaffold (2 poses, both RMSD <= 2.0)
        ScaffoldEvaluatedRecord(smiles="COc1ccccc1", rmsd=1.2, is_active=True, score=0.95),
        ScaffoldEvaluatedRecord(smiles="CCc1ccccc1", rmsd=1.8, is_active=True, score=0.91),
        # Cluster 2: Pyridine scaffold (2 poses, 1 <= 2.0, 1 > 2.0)
        ScaffoldEvaluatedRecord(smiles="COc1ccncc1", rmsd=1.5, is_active=False, score=0.60),
        ScaffoldEvaluatedRecord(smiles="CCc1ccncc1", rmsd=2.9, is_active=False, score=0.50),
        # Cluster 3: Naphthalene scaffold
        ScaffoldEvaluatedRecord(smiles="c1ccc2ccccc2c1", rmsd=2.4, is_active=False, score=0.40),
        ScaffoldEvaluatedRecord(smiles="Oc1ccc2ccccc2c1", rmsd=1.1, is_active=False, score=0.35),
        # Cluster 4: Indole scaffold
        ScaffoldEvaluatedRecord(smiles="c1ccc2[nH]ccc2c1", rmsd=0.9, is_active=False, score=0.30),
        # Cluster 5: Thiophene scaffold
        ScaffoldEvaluatedRecord(smiles="c1ccsc1", rmsd=3.4, is_active=False, score=0.25),
        # Cluster 6: Furan scaffold
        ScaffoldEvaluatedRecord(smiles="c1ccoc1", rmsd=1.9, is_active=False, score=0.20),
        # Cluster 7: Quinoline scaffold
        ScaffoldEvaluatedRecord(smiles="c1ccc2ncccc2c1", rmsd=1.4, is_active=False, score=0.10),
    ]

    summary = evaluate_benchmark_suite(records, seed=42, n_boot=300)
    assert summary["num_records"] == 10
    assert summary["num_scaffold_clusters"] == 7
    assert math.isclose(summary["rmsd_2a_pass_rate"], 0.7, abs_tol=1e-6)
    ci_low, ci_high = summary["rmsd_2a_ci95"]
    assert 0.0 <= ci_low <= summary["rmsd_2a_pass_rate"] <= ci_high <= 1.0
    # Top 10% of 10 = top 1 record (score=0.95 -> active! Baseline active rate 2/10 = 0.2 -> EF10% = 1.0 / 0.2 = 5.0)
    assert summary["ef10"] == 5.0


def test_ef10_returns_none_when_explicit_scores_missing_or_empty() -> None:
    records_no_score = [
        ScaffoldEvaluatedRecord(smiles="c1ccccc1", rmsd=1.2, is_active=True, score=None),
        ScaffoldEvaluatedRecord(smiles="c1ccncc1", rmsd=1.5, is_active=False, score=None),
    ]
    summary = evaluate_benchmark_suite(records_no_score, seed=42, n_boot=100)
    assert summary["ef10"] is None
    assert summary["rmsd_2a_pass_rate"] == 1.0

    empty_summary = evaluate_benchmark_suite([], seed=42, n_boot=50)
    assert empty_summary["num_records"] == 0
    assert empty_summary["rmsd_2a_pass_rate"] is None
    assert empty_summary["ef10"] is None
