---
trigger: always_on
description: Scientific integrity, epistemic tagging (Measured vs. Illustrative), dynamic mathematical metric derivations, AGPLv3 licensing, and NVIDIA non-affiliation disclaimers.
---

# Scientific Integrity, Parity & Regulatory Compliance

## 1. Epistemic Tagging & Visual Separation
- **Hardware-Measured Data (`Measured`):**
  - Applies exclusively to empirical hardware benchmark data captured on physical accelerator hardware (e.g., NVIDIA H100 80GB SXM5, AMD EPYC 7763).
  - Styling requirement: Solid green signal badges (`#76F5A2` or `#10B981`, `background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3)`).
- **Simulated / Illustrative Outputs (`Illustrative`):**
  - Applies to projected campaign savings, demo calculations, simulated token streams, and synthetic 3D backbone coordinates.
  - Styling requirement: Dashed ember/amber badge (`#FF8A4C`, `background: rgba(255, 138, 76, 0.15); border: 1px dashed rgba(255, 138, 76, 0.5)`).
- **Rule of Truth:** Never label a simulated, interpolated, or projected metric as "Measured" or "Empirical".

## 2. Dynamic Metric Derivation & Scientific Parity
- **Single Source of Truth:** All headline statistics, speedups, latencies, and savings must derive directly from `results/benchmark_summary.json`. Never hard-code conflicting numbers in HTML, documentation, or marketing copy.
- **Mathematical Formulations:**
  - **Geometric Mean Speedup:**
    $$\text{GeoMean} = \left(\prod_{i=1}^{n} S_i\right)^{\frac{1}{n}} = \exp\left(\frac{1}{n}\sum_{i=1}^{n} \ln(S_i)\right)$$
    Current verified benchmark geometric mean: **54.1x**.
  - **Arithmetic Mean Speedup:**
    $$\text{Mean} = \frac{1}{n}\sum_{i=1}^{n} S_i$$
    Current verified benchmark arithmetic mean: **54.8x**.
  - **End-to-End Cycle Time Saved (per 10,000 complexes):**
    $$\Delta T_{10\text{k}} = \frac{(t_{\text{CPU}} - t_{\text{NIM}}) \times 10{,}000}{3600} = \frac{(32.40\text{s} - 0.55\text{s}) \times 10{,}000}{3600} = 88.47 \approx \mathbf{88.5}\text{ hours}$$
  - **Total Compute Reduction Ratio:**
    $$\text{Reduction Ratio} = \frac{\sum t_{\text{CPU}}}{\sum t_{\text{NIM}}} = \frac{32.40}{0.55} \approx \mathbf{58.9\text{x}}$$
- **Audit Verification:** `scripts/audit/audit_release.py` enforces mathematical parity across `index.html`, `cockpit.html`, and `results/benchmark_summary.json`. Any divergence constitutes a blocking release failure.

## 3. Legal Attribution, Licensing & Trademark Compliance
- **AGPLv3 License Preservation:**
  - The repository and web cockpit are licensed under the GNU Affero General Public License v3.0 (`AGPL-3.0-only`).
  - The license reference and source repository link (`https://github.com/Jorwalzzz/bionemo-nim-benchmark`) must remain visible in all public web footers, CLI help strings, and exported dossiers.
- **Hermetic Test Suite Status:**
  - Preserve the hermetic test count reference (`101/101 HERMETIC TESTS PASSING`) across headers and badges. Any change to test counts must match actual passing test outputs.
- **Mandatory NVIDIA Non-Affiliation Disclaimer:**
  - The complete legal notice must appear prominently on all public entrypoints (`index.html`, `cockpit.html`, `README.md`, exported reports):
  > **NVIDIA Trademark & Non-Affiliation Notice:** NVIDIA, BioNeMo, NIM, TensorRT, and Hopper are trademarks and/or registered trademarks of NVIDIA Corporation in the United States and other jurisdictions. This open-source benchmark suite, web interface, and research evaluation are independently developed by Aarav Jorwal and are not sponsored, endorsed, certified, or affiliated with NVIDIA Corporation.
