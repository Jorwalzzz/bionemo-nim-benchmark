#!/usr/bin/env python3
"""
Quick execution script for BioNeMo benchmarks with rich summary output.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import BenchmarkPipeline

def main():
    print("=" * 80)
    print("NVIDIA BioNeMo Benchmark Profiler (Quick Runner)")
    print("=" * 80)

    data_path = PROJECT_ROOT / "data" / "sample_complexes.json"
    if not data_path.exists():
        print(f"Error: Could not find {data_path}")
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        complexes = json.load(f)

    print(f"Loaded {len(complexes)} target complexes for evaluation.")
    pipeline = BenchmarkPipeline(mock=True)

    header = f"{'Complex':<12} | {'Length':<8} | {'CPU Latency':<12} | {'NIM Latency':<12} | {'Speedup':<8} | {'Top Affinity':<14}"
    print(header)
    print("-" * len(header))

    for c in complexes:
        rec = pipeline.evaluate_complex(c, benchmark_runs=1)
        row = (
            f"{rec.complex_id:<12} | "
            f"{rec.residue_count:<8} | "
            f"{rec.cpu_total_latency_ms:>9.1f} ms | "
            f"{rec.nim_total_latency_ms:>9.1f} ms | "
            f"{rec.speedup_factor:>6.2f}x | "
            f"{rec.diffdock_top_affinity_kcal_mol:>10.2f} kcal/mol"
        )
        print(row)

    print("-" * len(header))
    print("Benchmark complete. For high-res plots and CSV export, run: python run_benchmark.py --save-plots")

if __name__ == "__main__":
    main()
