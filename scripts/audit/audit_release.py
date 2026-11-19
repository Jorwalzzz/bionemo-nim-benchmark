#!/usr/bin/env python3
"""
Release Audit & Scientific Parity Validator for bionemo-nim-benchmark.

Validates HTML entrypoints (index.html, cockpit.html) against:
1. GitHub Pages subpath safety (forbids root-relative `/...` asset paths; checks `./...` targets exist).
2. WCAG 2.2 AA structural baseline (missing `alt` on `<img>`, unlabeled `<input>`/`<button>`/`<svg>`, missing `lang`).
3. Mathematical & scientific parity between `results/benchmark_summary.json` and rendered HTML metrics.
"""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass
class AuditIssue:
    severity: str  # "ERROR" | "WARN"
    category: str  # "PATH" | "A11Y" | "PARITY"
    file: str
    line: int
    message: str


@dataclass
class HTMLAuditState:
    file_path: Path
    has_html_lang: bool = False
    asset_refs: list[tuple[int, str, str]] = field(default_factory=list)  # (line, attr, url)
    anchor_ids: set[str] = field(default_factory=set)
    internal_hashes: list[tuple[int, str]] = field(default_factory=list)
    label_fors: set[str] = field(default_factory=set)
    text_chunks: list[str] = field(default_factory=list)
    issues: list[AuditIssue] = field(default_factory=list)


class ReleaseHTMLParser(HTMLParser):
    """Single-pass HTML5 parser auditing asset paths, ARIA/alt rules, and text content."""

    PATH_ATTRS: frozenset[str] = frozenset({"src", "href", "poster", "data-src", "data-json", "data-csv"})
    SKIP_SCHEMES: frozenset[str] = frozenset({"http", "https", "mailto", "tel", "data", "blob", "javascript"})

    def __init__(self, state: HTMLAuditState) -> None:
        super().__init__(convert_charrefs=True)
        self.state = state
        self._in_script_or_style = False
        self._button_stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, _ = self.getpos()
        attr_map: dict[str, str] = {k.lower(): (v if v is not None else "") for k, v in attrs}

        if tag in {"script", "style"}:
            self._in_script_or_style = True

        if "id" in attr_map and attr_map["id"].strip():
            self.state.anchor_ids.add(attr_map["id"].strip())

        if tag == "html" and attr_map.get("lang", "").strip():
            self.state.has_html_lang = True

        if tag == "label" and attr_map.get("for", "").strip():
            self.state.label_fors.add(attr_map["for"].strip())

        # 1. Audit local vs root-relative paths
        for attr in self.PATH_ATTRS:
            if attr not in attr_map:
                continue
            raw_url = attr_map[attr].strip()
            if not raw_url:
                continue
            if raw_url.startswith("#"):
                if len(raw_url) > 1:
                    self.state.internal_hashes.append((line, raw_url[1:].split("?")[0]))
                continue
            parsed = urlparse(raw_url)
            if parsed.scheme.lower() in self.SKIP_SCHEMES or raw_url.startswith("//"):
                continue
            self.state.asset_refs.append((line, attr, raw_url))

        # 2. WCAG 2.2 AA structural checks
        if tag == "img" and "alt" not in attr_map:
            self.state.issues.append(
                AuditIssue(
                    severity="ERROR",
                    category="A11Y",
                    file=self.state.file_path.name,
                    line=line,
                    message="<img> element missing required `alt` attribute.",
                )
            )

        if tag == "input" and attr_map.get("type", "text").lower() != "hidden":
            has_aria = bool(attr_map.get("aria-label", "").strip() or attr_map.get("aria-labelledby", "").strip())
            has_title = bool(attr_map.get("title", "").strip())
            input_id = attr_map.get("id", "").strip()
            if not (has_aria or has_title or input_id):
                self.state.issues.append(
                    AuditIssue(
                        severity="ERROR",
                        category="A11Y",
                        file=self.state.file_path.name,
                        line=line,
                        message="<input> lacks `id` (for <label>), `aria-label`, or `aria-labelledby`.",
                    )
                )

        if tag == "svg":
            aria_hidden = attr_map.get("aria-hidden", "").lower() == "true"
            has_label = bool(attr_map.get("aria-label", "").strip() or attr_map.get("aria-labelledby", "").strip())
            role_img = attr_map.get("role", "").lower() == "img"
            if role_img and not has_label and not aria_hidden:
                self.state.issues.append(
                    AuditIssue(
                        severity="ERROR",
                        category="A11Y",
                        file=self.state.file_path.name,
                        line=line,
                        message='<svg role="img"> missing `aria-label` or `aria-labelledby`.',
                    )
                )

        if tag == "button":
            has_aria = bool(attr_map.get("aria-label", "").strip() or attr_map.get("aria-labelledby", "").strip())
            self._button_stack.append({"line": line, "has_aria": has_aria, "text": ""})

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._in_script_or_style = False
        if tag == "button" and self._button_stack:
            btn = self._button_stack.pop()
            if not btn["has_aria"] and not btn["text"].strip():
                self.state.issues.append(
                    AuditIssue(
                        severity="ERROR",
                        category="A11Y",
                        file=self.state.file_path.name,
                        line=btn["line"],
                        message="<button> has neither visible text content nor `aria-label`.",
                    )
                )

    def handle_data(self, data: str) -> None:
        if self._button_stack:
            self._button_stack[-1]["text"] += data
        if not self._in_script_or_style:
            self.state.text_chunks.append(data)


def validate_html_file(html_path: Path, repo_root: Path) -> HTMLAuditState:
    """Parse an HTML file and validate paths, fragments, and accessibility attributes."""
    state = HTMLAuditState(file_path=html_path)
    if not html_path.exists():
        state.issues.append(
            AuditIssue("ERROR", "PATH", html_path.name, 0, f"Required HTML file not found: {html_path}")
        )
        return state

    content = html_path.read_text(encoding="utf-8")
    parser = ReleaseHTMLParser(state)
    parser.feed(content)
    parser.close()

    if not state.has_html_lang:
        state.issues.append(
            AuditIssue("ERROR", "A11Y", html_path.name, 1, "<html> root tag missing `lang` attribute.")
        )

    for line, attr, raw_url in state.asset_refs:
        clean_path = raw_url.split("#")[0].split("?")[0]
        if clean_path.startswith("/"):
            state.issues.append(
                AuditIssue(
                    severity="ERROR",
                    category="PATH",
                    file=html_path.name,
                    line=line,
                    message=f"Forbidden root-relative path in `{attr}=\"{raw_url}\"`. Must use `./...` for GitHub Pages subpath safety.",
                )
            )
            continue

        resolved = (html_path.parent / clean_path).resolve()
        if not resolved.exists():
            state.issues.append(
                AuditIssue(
                    severity="ERROR",
                    category="PATH",
                    file=html_path.name,
                    line=line,
                    message=f"Broken relative reference `{attr}=\"{raw_url}\"` -> target missing on disk ({resolved.relative_to(repo_root) if resolved.is_relative_to(repo_root) else resolved}).",
                )
            )

    for line, target_id in state.internal_hashes:
        if target_id not in state.anchor_ids:
            state.issues.append(
                AuditIssue(
                    severity="WARN",
                    category="PATH",
                    file=html_path.name,
                    line=line,
                    message=f"Internal anchor `#{target_id}` does not match any `id` in {html_path.name}.",
                )
            )

    return state


def extract_benchmark_records(payload: Any) -> list[dict[str, Any]]:
    """Normalize common benchmark_summary.json schemas into a flat list of model records."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("benchmarks", "results", "models", "runs", "data"):
            if isinstance(payload.get(key), list):
                return [r for r in payload[key] if isinstance(r, dict)]
    return []


def audit_json_parity(json_path: Path, index_state: HTMLAuditState) -> list[AuditIssue]:
    """Verify mathematical consistency of benchmark_summary.json and check parity with index.html."""
    issues: list[AuditIssue] = []
    if not json_path.exists():
        issues.append(
            AuditIssue("ERROR", "PARITY", json_path.name, 0, f"Missing benchmark JSON source: {json_path}")
        )
        return issues

    try:
        raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(AuditIssue("ERROR", "PARITY", json_path.name, exc.lineno, f"Malformed JSON: {exc.msg}"))
        return issues

    records = extract_benchmark_records(raw_data)
    if not records:
        issues.append(
            AuditIssue("WARN", "PARITY", json_path.name, 1, "No benchmark record array found in JSON payload.")
        )
        return issues

    speedups: list[float] = []
    visible_text = " ".join(index_state.text_chunks)

    for idx, rec in enumerate(records, start=1):
        cpu_s = rec.get("cpu_time_s") or rec.get("cpu_s") or rec.get("cpu_latency_s")
        gpu_s = rec.get("gpu_time_s") or rec.get("h100_s") or rec.get("gpu_latency_s")
        recorded_speedup = rec.get("speedup") or rec.get("speedup_x")
        name = str(rec.get("model") or rec.get("nim") or rec.get("target") or f"row_{idx}")

        if isinstance(cpu_s, (int, float)) and isinstance(gpu_s, (int, float)) and gpu_s > 0:
            computed = cpu_s / gpu_s
            speedups.append(computed)
            if isinstance(recorded_speedup, (int, float)) and abs(computed - recorded_speedup) > 0.15:
                issues.append(
                    AuditIssue(
                        severity="ERROR",
                        category="PARITY",
                        file=json_path.name,
                        line=idx,
                        message=f"[{name}] Speedup mismatch: JSON stores {recorded_speedup:.2f}x, but cpu/gpu = {computed:.2f}x.",
                    )
                )

    if speedups:
        arith_mean = sum(speedups) / len(speedups)
        geom_mean = math.exp(sum(math.log(s) for s in speedups) / len(speedups))
        mean_str = f"{arith_mean:.1f}"
        geomean_str = f"{geom_mean:.1f}"

        if visible_text and mean_str not in visible_text:
            issues.append(
                AuditIssue(
                    severity="WARN",
                    category="PARITY",
                    file=index_state.file_path.name,
                    line=0,
                    message=f"Computed arithmetic mean speedup ({mean_str}x) not found in static HTML text (verify JS hydrator sets it).",
                )
            )
        if visible_text and geomean_str not in visible_text:
            issues.append(
                AuditIssue(
                    severity="WARN",
                    category="PARITY",
                    file=index_state.file_path.name,
                    line=0,
                    message=f"Computed geometric mean speedup ({geomean_str}x) not found in static HTML text (verify JS hydrator sets it).",
                )
            )

    # Check for unguarded MRTX1133 MW discrepancy if both 378.5 and 601.7 appear without scaffold context
    if "378.5" in visible_text and "601.7" in visible_text and not re.search(r"scaffold|core", visible_text, re.I):
        issues.append(
            AuditIssue(
                severity="WARN",
                category="PARITY",
                file=index_state.file_path.name,
                line=0,
                message="Both 378.5 and 601.7 MW values appear in HTML without explicit 'core/scaffold' vs 'full ligand' labels.",
            )
        )

    return issues


def find_repo_root() -> Path:
    """Resolve repository root directory reliably from current script location."""
    for p in Path(__file__).resolve().parents:
        if (p / "index.html").exists() and (p / "results").exists():
            return p
    return Path(__file__).resolve().parent.parent.parent


def main() -> int:
    repo_root = find_repo_root()
    index_path = repo_root / "index.html"
    cockpit_path = repo_root / "cockpit.html"
    json_path = repo_root / "results" / "benchmark_summary.json"

    index_state = validate_html_file(index_path, repo_root)
    cockpit_state = validate_html_file(cockpit_path, repo_root)
    parity_issues = audit_json_parity(json_path, index_state)

    all_issues = index_state.issues + cockpit_state.issues + parity_issues
    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARN"]

    print("=" * 76)
    print(f"RELEASE AUDIT REPORT | Root: {repo_root}")
    print(f"Summary: {len(errors)} ERROR(S), {len(warnings)} WARNING(S)")
    print("=" * 76)

    if not all_issues:
        print("[PASS] Zero broken paths, zero WCAG attribute errors, and full JSON parity verified.")
        return 0

    for issue in all_issues:
        loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
        print(f"[{issue.severity:<5}] [{issue.category:<6}] {loc:<22} -> {issue.message}")

    print("-" * 76)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
