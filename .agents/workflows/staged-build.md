---
description: Bounded staged feature engineering protocol decomposing changes into data contracts (Stage 1) and UI integration (Stage 2) with mandatory stop-and-review gates.
---

# /staged-build Workflow: Atomic Staged Feature Engineering

Execute this workflow whenever `/staged-build` is invoked or when implementing complex features spanning more than 3 files.

## Workflow Phases & Review Gates

### Stage 0: Pre-Flight Audit & Baseline Verification
1. Inspect git status and ensure working tree is clean:
   ```powershell
   git status --short
   ```
2. Run baseline verification:
   ```powershell
   python scripts/audit/audit_release.py
   ```
3. Formulate an implementation plan listing target files, data contracts, and verification commands.

### Stage 1: Data Contracts, Schemas & Core Logic
1. Implement or modify only the core backend models, API clients, or schema files:
   - Data structures in `src/bionemo_benchmark/`
   - Data summaries in `results/benchmark_summary.json`
2. Strict Zero-Placeholder Law applies: 100% complete, runnable code with zero `# TODO` or stubbed blocks.
3. Verify in terminal:
   ```powershell
   python -m py_compile <modified_files>
   ```
4. **STOP-AND-REVIEW CHECKPOINT 1:**
   Present a 3-column diff table:
   | File | Action | Exact Change |
   | :--- | :---: | :--- |
   Halt and request owner confirmation before proceeding to Stage 2.

### Stage 2: UI Components, Styling & Relative Path Integration
1. Implement frontend templates and scripts in `index.html`, `cockpit.html`, `css/`, or `js/`.
2. Strictly enforce relative paths (`./css/...`, `./js/...`, `./data/...`).
3. Apply Bio-Precision Obsidian Lab design system (`#05070A` canvas, `#76F5A2` green, `#5CE1FF` cyan).
4. Verify in terminal:
   ```powershell
   python scripts/audit/audit_release.py
   ```
5. **STOP-AND-REVIEW CHECKPOINT 2:**
   Present visual inspection findings and HTML validation status.

### Stage 3: End-to-End Release Gate Verification
1. Execute final audit:
   ```powershell
   python scripts/audit/audit_release.py
   ```
2. Confirm zero errors, zero warnings, and full JSON parity.
3. Conclude with completion summary.
