# BioNeMo Benchmark Metrics & Plotting Reference

## 1. Plotting Specifications
- Resolution: 300 DPI (`plt.savefig(path, dpi=300, bbox_inches='tight')`)
- Palettes: NVIDIA Green (`#76B900`), Slate Grey (`#4A5568`), Accent Teal (`#00A389`).
- Font sizes: Title: 14pt, Axis Labels: 12pt, Tick Labels: 10pt.

## 2. Benchmark Visualizations
- **Throughput Comparison (`results/throughput_comparison.png`)**:
  - Grouped bar chart comparing CPU baseline vs. NVIDIA NIM token throughput ($\text{tokens}/\text{sec}$).
  - Annotated speedup factor labels (`2.4x`, `2.0x`) on top of bars.
- **Latency vs. Sequence Length (`results/latency_vs_length.png`)**:
  - Line plot illustrating quadratic trend for CPU compute vs flat/linear scaling for GPU TensorRT-LLM.
  - Filled area showing network overhead vs compute time.
