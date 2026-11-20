---
name: staged-execution-guard
description: "Enforce atomic staged execution protocols for multi-file engineering tasks (> 3 files): decompose complex tasks into bounded sequential phases, mandate terminal verification gates at each boundary, and require explicit review checkpoints before proceeding."
---

# Staged Execution Guard Protocol

This skill enforces strict engineering boundaries on multi-file changes, preventing runaway generation, untested cascading diffs, and generic placeholder templates.

## 1. Activation Trigger
This protocol automatically activates whenever a task involves:
- Modifying or creating **more than 3 files** across the repository.
- Altering core data contracts (`results/benchmark_summary.json`, server API schemas).
- Modifying cross-module interfaces (e.g. between `bionemo_benchmark.core` and `bionemo_benchmark.mcp`).
- Large-scale UI rewrites impacting both `index.html` and `cockpit.html`.

## 2. The 4-Phase Staged Execution Framework

```
  Phase 0: Audit & Baseline Verification
                   │
                   ▼
  Phase 1: Data Contracts, Schemas & Core Logic
                   │  ◄── [Terminal Verification Gate & Checkpoint]
                   ▼
  Phase 2: UI Components, Visual Rendering & Integration
                   │  ◄── [Terminal Verification Gate & Checkpoint]
                   ▼
  Phase 3: End-to-End Release Audits & Parity Checks
```

### Phase 0: Audit & Baseline Verification
- Read existing target files and caller modules.
- Run baseline verification: `python scripts/audit/audit_release.py`.
- Formulate an explicit plan identifying the target files, blast radius, and test targets.

### Phase 1: Data Contracts & Core Logic
- Implement schemas, domain models, algorithms, and pure utility functions.
- **Rule:** Write 100% complete, runnable code with zero placeholders (`# TODO`, `pass`).
- **Gate:** Execute unit tests on the changed modules.
- **Checkpoint:** Halt and present a Stage 1 summary table before touching any downstream UI or client code.

### Phase 2: UI, Styling & Integration
- Implement frontend templates, CSS styling, and JavaScript consumers using the `frontend-obsidian-lab` skill.
- Ensure all asset references are strictly relative (`./...`).
- **Gate:** Run HTML release parser and viewport audits.
- **Checkpoint:** Halt and present visual verification results before finalizing.

### Phase 3: Comprehensive Verification & Release Gating
- Execute the complete unified release audit:
  ```powershell
  python scripts/audit/audit_release.py
  ```
- Verify zero broken paths, zero WCAG contrast/alt errors, and complete scientific metric parity.
- Confirm clean git status.

## 3. Stop-and-Review Checkpoint Contract
At each phase boundary, the agent must present:
1. **Executed Changes:** Exact files modified and lines added/changed.
2. **Verification Evidence:** Terminal command output showing exit code `0`.
3. **Pending Actions:** The exact files and logic planned for the subsequent phase.
4. **Confirmation Request:** Ask the user/operator for confirmation before proceeding to the next stage.
