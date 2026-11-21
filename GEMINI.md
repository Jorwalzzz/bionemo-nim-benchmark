# BIONEMO-NIM-BENCHMARK: CANONICAL WORKSPACE CONSTITUTION

This document establishes project-wide invariants operating at highest workspace precedence across all Antigravity agent sessions.

## 1. Zero-Placeholder Law (Non-Negotiable)
- **Strictly Banned:** `// TODO`, `# ... rest of implementation`, `pass` stubs, truncated functions, elided imports, or mock placeholder logic where functional code is expected.
- **Pass-1 Completeness:** Every file authored or edited must be 100% complete, fully implemented, syntactically valid, and immediately runnable.
- **Surgical Changes:** Make exact, minimal edits without destroying working logic or substituting full blocks with summary comments.

## 2. GitHub Pages Relative Path Discipline (`./`)
- **Strictly Relative Paths:** Every internal URL reference (`href`, `src`, `data-*`, `fetch()`, `url()`) across `index.html`, `cockpit.html`, CSS, and JavaScript MUST use strictly relative paths (`./css/...`, `./js/...`, `./data/...`, `./assets/...`).
- **Forbidden Root Paths:** Root-relative paths (`/css/...`, `/assets/...`) are strictly forbidden. The production deployment is hosted under the subpath `https://jorwalzzz.github.io/bionemo-nim-benchmark/`. Root-relative paths resolve to `jorwalzzz.github.io/` and result in broken HTTP 404 asset requests.

## 3. Mandatory Terminal Proof Gate
- Never declare a task complete without executing terminal verification and confirming exit code `0`.
- Release Gate Command:
  ```powershell
  python scripts/audit/audit_release.py
  ```
- Before delivering changes to web assets or scientific metrics, this audit must pass with 0 errors and 0 warnings.

## 4. Epistemic Tagging: Measured vs. Illustrative
- **Measured (Empirical Data):** Captured on physical accelerator hardware (NVIDIA H100 80GB SXM5 / AMD EPYC 7763). Rendered as solid green badges (`#76F5A2` or `#10B981`, `background: rgba(16, 185, 129, 0.15)`).
- **Illustrative (Projected / Demo):** Projections, extrapolations, simulated token streams, and synthetic backbones. Rendered as dashed ember badges (`#FF8A4C`, `border: 1px dashed rgba(255, 138, 76, 0.5)`).
- Never label simulated, interpolated, or projected metrics as "Measured".

## 5. Scientific Parity & Regulatory Attribution
- **Single Source of Truth:** All speedup metrics, geometric means (54.1x), and campaign hours saved (88.5h / 10k) must derive directly from `results/benchmark_summary.json`.
- **License & Tests:** Preserve the AGPLv3 license notices and the 186/186 hermetic test count across public views.
- **Mandatory Trademark Disclaimer:** The full legal notice must appear on all public entrypoints:
  > **NVIDIA Trademark & Non-Affiliation Notice:** NVIDIA, BioNeMo, NIM, TensorRT, and Hopper are trademarks and/or registered trademarks of NVIDIA Corporation in the United States and other jurisdictions. This open-source benchmark suite, web interface, and research evaluation are independently developed by Aarav Jorwal and are not sponsored, endorsed, certified, or affiliated with NVIDIA Corporation.
