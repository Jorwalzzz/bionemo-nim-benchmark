---
trigger: always_on
description: Core engineering discipline, zero-placeholder law, GitHub Pages relative path safety, and mandatory terminal release gates.
---

# Engineering Discipline & Execution Rules

## 1. Grounded Inspection Before Generation
- **Audit Before Write:** Always read target files, callers, dependencies, and test suites using exact paths before authoring or modifying code. Never assume function signatures, exported constants, or file layouts.
- **Minimal Blast Radius:** Confine edits strictly to the files directly responsible for the requested feature or fix. Never execute blanket formatting sweeps, unrequested refactors, or rename public identifiers without explicit authorization.
- **Dependency Hygiene:** Never introduce phantom third-party libraries. Verify installed packages against `pyproject.toml` and the active environment before importing.

## 2. Zero-Placeholder & Production-Completeness Law
- **Strictly Banned:** `// TODO`, `# ... rest of implementation`, `pass` stubs, truncated functions, elided imports, or mock placeholder logic where functional code is expected.
- **Pass-1 Completeness:** Every file created or edited must be 100% complete, fully implemented, syntactically valid, and immediately runnable.
- **Surgical Edits:** Apply exact, minimal diffs. Never overwrite working code blocks with summary comments or placeholders.

## 3. GitHub Pages Subpath & Asset Safety
- **Strictly Relative Paths:** All static web assets (`href`, `src`, `url()`, `fetch()`, `data-*`) in `HTML`, `CSS`, and clientside `JS` must use strictly relative paths (`./css/...`, `./js/...`, `./data/...`, `./assets/...`).
- **Forbidden Root Paths:** Never use root-relative paths (`/css/...`, `/assets/...`, `/data/...`). On GitHub Pages, this repository is hosted at `https://jorwalzzz.github.io/bionemo-nim-benchmark/`; root-relative paths resolve to `jorwalzzz.github.io/` and result in catastrophic HTTP 404 asset failures.
- **Anchor & Asset Verification:** All internal hash fragments (`#target`) must correspond to valid existing `id` attributes. All referenced local files must exist in the repository tree.

## 4. Terminal Verification Gate
- **Closed-Loop Execution:** Writing code is only the first step. Every change must be validated in the terminal before declaring completion.
- **Audit Suite Execution:** Execute `python scripts/audit/run_all_audits.py` or `python scripts/audit/audit_release.py`. The release audit verifies:
  1. Zero broken local file paths and zero root-relative path violations.
  2. WCAG 2.2 AA accessibility structural compliance (`lang` attribute, image `alt` texts, form control labels).
  3. Mathematical parity between `results/benchmark_summary.json` and rendered DOM metrics.
- **Zero-Failure Gate:** If any audit or test returns a non-zero exit code, diagnose the traceback, apply the fix, and re-run until exit code `0` is achieved.

## 5. Response Formatting & Live Telemetry Protocol
- **Top Status Bar:** Open every response with a concise mission-control status bar:
  `[PHASE: <Name>] | Workspace: bionemo-nim-benchmark | Status: <ACTIVE / VERIFYING / COMPLETE>`
- **Live Checklist:** Maintain an explicit status checklist for multi-step tasks:
  - `[✓]` Completed step
  - `[▶]` Currently active step
  - `[ ]` Queued step
  - `[!]` Blocked / flag step
- **3-Column File-Diff Summary Table:** Conclude changes with a structured table:
  | File | Action | Exact Change |
  | :--- | :---: | :--- |
- **Single-Level Bullets:** Format bulleted explanations with clean single-level items (`- **Key:** Value`) and zero blank lines between bullets.
