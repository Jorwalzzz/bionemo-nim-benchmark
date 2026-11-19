"""
Deterministic unit tests for Core Metrics, Statistical Aggregation, and Plotting.
Part of NVIDIA BioNeMo Benchmark Suite.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from bionemo_benchmark.core.metrics import (
    BenchmarkReporter,
    calculate_speedup,
    compute_summary_statistics,
)


class MockBenchmarkRecord:
    """Mock record matching ComplexBenchmarkRecord interface for hermetic testing."""

    def __init__(
        self,
        target_name: str,
        residue_count: int,
        nim_lat: float,
        cpu_lat: float,
        nim_tps: float,
        cpu_tps: float,
        speedup: float,
        diffdock_lat: float,
    ):
        self._dict = {
            "target_name": target_name,
            "residue_count": residue_count,
            "nim_total_latency_ms": nim_lat,
            "cpu_total_latency_ms": cpu_lat,
            "nim_tokens_per_sec": nim_tps,
            "cpu_tokens_per_sec": cpu_tps,
            "speedup_factor": speedup,
            "throughput_improvement_ratio": speedup,
            "diffdock_latency_ms": diffdock_lat,
        }

    def to_dict(self):
        return self._dict


class TestComputeSummaryStatistics:
    """Verifies statistical profiling across standard and edge-case inputs."""

    def test_empty_list_returns_zero_dict(self):
        stats = compute_summary_statistics([])
        assert stats == {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p95": 0.0,
        }

    def test_single_value(self):
        stats = compute_summary_statistics([42.0])
        assert stats["mean"] == 42.0
        assert stats["median"] == 42.0
        assert stats["std"] == 0.0
        assert stats["min"] == 42.0
        assert stats["max"] == 42.0
        assert stats["p95"] == 42.0

    def test_identical_values(self):
        stats = compute_summary_statistics([10.5, 10.5, 10.5, 10.5])
        assert stats["mean"] == 10.5
        assert stats["median"] == 10.5
        assert stats["std"] == 0.0
        assert stats["min"] == 10.5
        assert stats["max"] == 10.5
        assert stats["p95"] == 10.5

    def test_normal_distribution_profile(self):
        vals = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = compute_summary_statistics(vals)
        assert stats["mean"] == 30.0
        assert stats["median"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["std"] > 0.0
        assert stats["p95"] > stats["median"]

    def test_negative_values(self):
        vals = [-10.5, -8.2, -12.1, -5.0]
        stats = compute_summary_statistics(vals)
        assert stats["min"] == -12.1
        assert stats["max"] == -5.0
        assert stats["mean"] < 0.0


class TestCalculateSpeedup:
    """Verifies speedup factor computation and zero/negative division guards."""

    def test_standard_speedup(self):
        assert calculate_speedup(100.0, 10.0) == 10.0
        assert calculate_speedup(45.5, 1.5) == 30.33

    def test_zero_gpu_time_division_guard(self):
        assert calculate_speedup(100.0, 0.0) == 0.0
        assert calculate_speedup(0.0, 0.0) == 0.0

    def test_negative_gpu_time_guard(self):
        assert calculate_speedup(100.0, -5.0) == 0.0

    def test_fractional_speedup_where_gpu_slower(self):
        res = calculate_speedup(5.0, 10.0)
        assert res == 0.5


class TestBenchmarkReporter:
    """Verifies CSV generation and publication-grade Seaborn plotting with isolated paths."""

    @pytest.fixture
    def sample_records(self) -> list[MockBenchmarkRecord]:
        return [
            MockBenchmarkRecord("KRAS_G12D", 168, 35.0, 850.0, 4800.0, 197.6, 24.28, 22.5),
            MockBenchmarkRecord("SARS_CoV_2_Mpro", 306, 58.0, 1680.0, 5200.0, 182.1, 28.97, 37.0),
        ]

    def test_export_csv_to_tmp_dir(self, tmp_path: Path, sample_records: list[MockBenchmarkRecord]):
        out_dir = str(tmp_path / "metrics_test")
        reporter = BenchmarkReporter(sample_records, output_dir=out_dir)
        csv_file = reporter.export_csv("summary_test.csv")

        assert os.path.isfile(csv_file)
        with open(csv_file, encoding="utf-8") as f:
            header = f.readline()
            assert "target_name" in header
            assert "speedup_factor" in header
            rows = f.readlines()
            assert len(rows) == 2

    def test_get_aggregate_stats(self, tmp_path: Path, sample_records: list[MockBenchmarkRecord]):
        reporter = BenchmarkReporter(sample_records, output_dir=str(tmp_path))
        stats = reporter.get_aggregate_stats()

        assert "speedup_stats" in stats
        assert "nim_throughput_stats" in stats
        assert stats["speedup_stats"]["mean"] > 20.0
        assert stats["nim_throughput_stats"]["max"] >= 5200.0

    def test_plot_throughput_comparison_to_tmp_dir(self, tmp_path: Path, sample_records: list[MockBenchmarkRecord]):
        out_dir = str(tmp_path / "plots")
        reporter = BenchmarkReporter(sample_records, output_dir=out_dir)
        plot_path = reporter.plot_throughput_comparison("throughput.png")

        assert os.path.isfile(plot_path)
        assert os.path.getsize(plot_path) > 1000

    def test_plot_latency_vs_length_to_tmp_dir(self, tmp_path: Path, sample_records: list[MockBenchmarkRecord]):
        out_dir = str(tmp_path / "plots")
        reporter = BenchmarkReporter(sample_records, output_dir=out_dir)
        plot_path = reporter.plot_latency_vs_length("scaling.png")

        assert os.path.isfile(plot_path)
        assert os.path.getsize(plot_path) > 1000
