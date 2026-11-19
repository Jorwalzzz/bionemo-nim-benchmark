#!/usr/bin/env python3
"""
Unified Stage E Release Audit Runner for bionemo-nim-benchmark.

Executes `scripts/audit/audit_release.py` and `scripts/audit/verify_viewports.py` sequentially
using the active Python interpreter (`sys.executable`), streams diagnostic logs on
failure, and prints a copy-ready Markdown summary table for the final release report.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SuiteResult:
    name: str
    script_rel: str
    exit_code: int
    duration_s: float
    highlights: str
    stdout: str
    stderr: str

    @property
    def status_badge(self) -> str:
        return "PASS" if self.exit_code == 0 else "FAIL"


def extract_highlights(script_name: str, stdout: str, stderr: str, exit_code: int) -> str:
    """Parse concise metrics from child audit stdout/stderr for the Markdown report."""
    combined = f"{stdout}\n{stderr}"

    if script_name == "audit_release.py":
        match = re.search(r"Summary:\s*(\d+)\s*ERROR\(S\),\s*(\d+)\s*WARNING\(S\)", combined)
        if match:
            errs, warns = match.group(1), match.group(2)
            return f"{errs} errors, {warns} warnings (paths, WCAG attrs, JSON parity)"

    if script_name == "verify_viewports.py":
        match = re.search(
            r"Total Checks:\s*(\d+)\s*\|\s*Passed:\s*(\d+)\s*\|\s*Failed:\s*(\d+)", combined
        )
        if match:
            total, passed, failed = match.group(1), match.group(2), match.group(3)
            return f"{passed}/{total} viewport-theme checks passed ({failed} failed); PNGs in `audit/screenshots/`"
        if "Playwright is not installed" in combined:
            return "Playwright missing (`pip install playwright && playwright install chromium`)"

    if exit_code != 0:
        first_err = next((line.strip() for line in stderr.splitlines() if line.strip()), "")
        return first_err[:90] if first_err else f"Exited with code {exit_code}"

    return "Completed cleanly"


def run_suite(name: str, script_path: Path, repo_root: Path) -> SuiteResult:
    """Execute a child verification script via subprocess and capture timing and output."""
    rel_path = str(script_path.relative_to(repo_root))
    if not script_path.exists():
        return SuiteResult(
            name=name,
            script_rel=rel_path,
            exit_code=127,
            duration_s=0.0,
            highlights=f"Missing script: `{rel_path}`",
            stdout="",
            stderr=f"FileNotFoundError: {script_path}",
        )

    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - t0
    highlights = extract_highlights(script_path.name, proc.stdout, proc.stderr, proc.returncode)

    return SuiteResult(
        name=name,
        script_rel=rel_path,
        exit_code=proc.returncode,
        duration_s=elapsed,
        highlights=highlights,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def render_markdown_table(results: list[SuiteResult]) -> str:
    """Format audit results as a clean, copy-ready GitHub Flavored Markdown table."""
    lines = [
        "### Automated Release Verification Summary",
        "",
        "| Verification Suite | Script | Status | Duration | Key Findings |",
        "| :--- | :--- | :---: | :---: | :--- |",
    ]
    for res in results:
        lines.append(
            f"| {res.name} | `{res.script_rel}` | **{res.status_badge}** | "
            f"`{res.duration_s:.2f}s` | {res.highlights} |"
        )
    overall = "READY FOR DEPLOYMENT" if all(r.exit_code == 0 for r in results) else "BLOCKED — FIX FAILURES ABOVE"
    lines.extend(["", f"**Release Gate:** `{overall}`"])
    return "\n".join(lines)


def find_repo_root() -> Path:
    """Resolve repository root directory reliably from current script location."""
    for p in Path(__file__).resolve().parents:
        if (p / "index.html").exists() and (p / "results").exists():
            return p
    return Path(__file__).resolve().parent.parent.parent


def main() -> int:
    repo_root = find_repo_root()
    audit_dir = repo_root / "scripts" / "audit"

    suites = [
        ("Static Path, WCAG & JSON Parity", audit_dir / "audit_release.py"),
        ("Playwright Multi-Viewport & Theme", audit_dir / "verify_viewports.py"),
    ]

    results: list[SuiteResult] = []
    for label, path in suites:
        print(f"[RUN] {label} ({path.relative_to(repo_root)})...")
        res = run_suite(label, path, repo_root)
        results.append(res)
        if res.exit_code != 0:
            print(f"\n--- DIAGNOSTIC LOG: {res.script_rel} (exit {res.exit_code}) ---")
            if res.stdout.strip():
                print(res.stdout.strip())
            if res.stderr.strip():
                print(res.stderr.strip(), file=sys.stderr)
            print("-" * 64 + "\n")

    print("\n" + render_markdown_table(results) + "\n")
    return 0 if all(r.exit_code == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
