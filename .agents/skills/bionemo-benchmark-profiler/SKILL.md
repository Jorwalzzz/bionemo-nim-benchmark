---
name: bionemo-benchmark-profiler
description: >-
  Use this skill when benchmarking, profiling, or analyzing performance of NVIDIA BioNeMo & NIM
  inference against baseline CPU compute. Covers token throughput calculation, latency scaling
  with sequence length, P95/P99 latency distribution, speedup multipliers, and generating
  publication-grade 300 DPI Seaborn plots.
---

# NVIDIA BioNeMo Benchmark & Profiler

This skill guides the execution, profiling, and comparative analysis of biological foundation models running on NVIDIA NIM (TensorRT-LLM on GPU) versus local CPU baselines.

## Quick Execution

### 1. Zero-Configuration Mock Benchmark (CI/CD / Fast Verification)
```bash
python run_benchmark.py --mock --save-plots
```
Generates:
- `results/benchmark_summary.csv`: Tabular latency, throughput, and docking metrics.
- `results/throughput_comparison.png`: High-resolution token throughput comparison.
- `results/latency_vs_length.png`: Latency scaling vs protein sequence length.

### 2. Live NVIDIA Cloud NIM Benchmark
```bash
python run_benchmark.py --api-key nvapi-xxxxxx --iterations 3 --save-plots
```

### 3. Quick CLI Profiler Helper
Run the standalone helper script:
```bash
python .agents/skills/bionemo-benchmark-profiler/scripts/quick_benchmark.py
```

---

## Benchmark Metrics & Profiling Methodology

1. **Token Throughput ($\text{tokens}/\text{sec}$)**:
   $$\text{Throughput} = \frac{L}{\Delta t_{\text{inference}}}$$
   Where $L$ is sequence length (residues) and $\Delta t$ is total elapsed time in seconds.

2. **Per-Residue Latency ($ms/\text{residue}$)**:
   $$\text{Per-Residue Latency} = \frac{\Delta t_{\text{ms}}}{L}$$

3. **Hardware Acceleration Speedup**:
   $$\text{Speedup} = \frac{\text{CPU Latency (FP32)}}{\text{NIM GPU Latency (TensorRT-LLM)}}$$

4. **Latency Breakdown**:
   - $\text{Server Inference Time}$: Actual GPU execution measured by remote headers.
   - $\text{Network Round-Trip Time}$: Wire latency = Total Latency - Server Inference Time.

---

## Detailed References
- [Metrics & Plotting Guide](./references/metrics_guide.md): Seaborn styling, statistical parameters, and speedup math.
- [Standalone Profiler Script](./scripts/quick_benchmark.py): Lightweight benchmark runner with formatted tabular output.
