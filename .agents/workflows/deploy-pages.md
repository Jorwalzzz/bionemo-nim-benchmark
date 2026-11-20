---
description: Safe production release to GitHub Pages requiring audit pass, forbidding force-pushes, executing --no-ff merge into main, and verifying live URL markers.
---

# /deploy-pages Workflow: Safe Production Release to GitHub Pages

Execute this workflow whenever `/deploy-pages` or `/deploy` is invoked to publish benchmark updates to `https://jorwalzzz.github.io/bionemo-nim-benchmark/`.

## Deployment Safety Protocol

### Step 1: Pre-Deployment Release Gate Audit
1. Verify working directory is repository root.
2. Confirm working tree has no uncommitted unstaged modifications:
   ```powershell
   git status --porcelain
   ```
3. Run the complete release audit suite:
   ```powershell
   python scripts/audit/audit_release.py
   ```
   **CRITICAL GATE:** If `audit_release.py` returns any errors or warnings, **ABORT IMMEDIATELY**. Do not proceed with merge or push.

### Step 2: Safe Git Branch Merge
1. Ensure the active branch is up to date:
   ```powershell
   git fetch origin
   ```
2. Checkout main and perform a safe, non-fast-forward merge:
   ```powershell
   git checkout main
   git merge --no-ff <feature-branch> -m "release: update benchmark artifacts and release cockpit"
   ```
3. **STRICT RULE:** Never use `git push --force` or `--force-with-lease`. Force-pushing to `main` is strictly prohibited.

### Step 3: Push to GitHub Remote
1. Push merged commits to origin:
   ```powershell
   git push origin main
   ```

### Step 4: Post-Deployment Live Verification
1. Query the live GitHub Pages URL:
   ```powershell
   python scripts/audit/audit_live_site.py
   ```
2. Verify HTTP 200 response status from `https://jorwalzzz.github.io/bionemo-nim-benchmark/`.
3. Verify live presence of critical content markers:
   - `BioNeMo NIM`
   - `101/101 HERMETIC TESTS PASSING`
   - `GNU Affero General Public License v3.0`
   - `NVIDIA Trademark & Non-Affiliation Notice`
