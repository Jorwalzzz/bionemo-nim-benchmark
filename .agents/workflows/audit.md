---
description: Non-destructive workspace audit running audit_release.py and run_all_audits.py to verify path safety, WCAG 2.2 AA accessibility, and scientific metric parity.
---

# /audit Workflow: Unified Workspace & Release Audit

Execute this workflow whenever `/audit` is invoked. This workflow performs non-destructive, read-only verification across static assets, WCAG accessibility, and scientific metric parity.

## Execution Procedure

### Step 1: Pre-Flight Environment Inspection
- Verify working directory is repository root:
  ```powershell
  Get-Location
  ```

### Step 2: Run Unified Release Audits
- Run the primary release audit suite:
  ```powershell
  python scripts/audit/audit_release.py
  ```
- If available, execute the complete test suite and multi-viewport checker:
  ```powershell
  python scripts/audit/run_all_audits.py
  ```

### Step 3: Parse & Format Results Table
Format the command outputs into a clean Markdown table:

| Verification Suite | Target File | Status | Duration | Key Findings |
| :--- | :--- | :---: | :---: | :--- |
| **Path Safety** | `index.html`, `cockpit.html` | PASS / FAIL | `<time>s` | Root-relative path check (`./...` strictly enforced) |
| **WCAG 2.2 AA** | `index.html`, `cockpit.html` | PASS / FAIL | `<time>s` | `alt` tags, `aria-label`, `<label for>`, `html[lang]` |
| **Scientific Parity** | `results/benchmark_summary.json` | PASS / FAIL | `<time>s` | Speedups, geometric means, hours saved parity |

### Step 4: Gate Verdict
- If all checks exit with code `0`:
  `Release Gate: PASS — READY FOR RELEASE`
- If any check returns non-zero:
  `Release Gate: BLOCKED — SEE DIAGNOSTIC LOGS ABOVE`
  List the exact file, line number, and corrective action needed. Zero files are modified during this workflow.
