#!/usr/bin/env python3
"""
Multi-Viewport, Theme & Console Verification Script for bionemo-nim-benchmark.

Spins up an ephemeral local HTTP server rooted at the repository directory,
renders `index.html` and `cockpit.html` in headless Chromium across desktop
(1440x900) and mobile (390x844) viewports in both Dark and Light themes,
audits horizontal overflow and console/uncaught page errors, and captures
screenshots into `audit/screenshots/`.
"""

from __future__ import annotations

import functools
import http.server
import socketserver
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    from playwright.sync_api import Page, sync_playwright
except ImportError as exc:
    raise SystemExit(
        "Playwright is not installed. Run:\n"
        "  pip install playwright && playwright install chromium"
    ) from exc


ThemeMode = Literal["dark", "light"]


@dataclass
class ViewportSpec:
    name: str
    width: int
    height: int
    is_mobile: bool
    device_scale_factor: int = 2


@dataclass
class PageAuditResult:
    page_name: str
    viewport: str
    theme: ThemeMode
    screenshot_path: Path
    overflow_px: int = 0
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.overflow_px <= 0 and not self.console_errors and not self.page_errors


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves static files without spamming stdout with every 200 OK asset request."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class ThreadedStaticServer:
    """Context-managed ephemeral HTTP server bound to 127.0.0.1 on an OS-assigned port."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        handler = functools.partial(QuietHTTPRequestHandler, directory=str(root_dir))
        self._httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        self._httpd.allow_reuse_address = True
        self.port: int = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def __enter__(self) -> ThreadedStaticServer:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=3.0)


def apply_theme_and_settle(page: Page, theme: ThemeMode) -> None:
    """Synchronize colorScheme, localStorage, and data-theme/class attributes, then settle layout."""
    page.emulate_media(color_scheme=theme)
    page.evaluate(
        """(targetTheme) => {
            try {
                localStorage.setItem('theme', targetTheme);
                localStorage.setItem('bionemo-theme', targetTheme);
            } catch (_) {}
            document.documentElement.setAttribute('data-theme', targetTheme);
            document.documentElement.classList.toggle('light', targetTheme === 'light');
            document.documentElement.classList.toggle('dark', targetTheme === 'dark');
            if (document.body) {
                document.body.setAttribute('data-theme', targetTheme);
            }
        }""",
        theme,
    )
    # Trigger scroll-based IntersectionObserver reveals and allow CSS transitions (180-400ms) to finish
    page.evaluate(
        """async () => {
            const totalHeight = document.documentElement.scrollHeight;
            const step = Math.max(window.innerHeight, 400);
            for (let y = 0; y <= totalHeight; y += step) {
                window.scrollTo(0, y);
                await new Promise((r) => setTimeout(r, 60));
            }
            window.scrollTo(0, 0);
        }"""
    )
    page.wait_for_timeout(450)


def measure_horizontal_overflow(page: Page) -> int:
    """Return max horizontal overflow in pixels (0 means zero horizontal clipping/scroll)."""
    return int(
        page.evaluate(
            """() => {
                const docWidth = document.documentElement.scrollWidth;
                const bodyWidth = document.body ? document.body.scrollWidth : 0;
                const viewportWidth = window.innerWidth;
                return Math.max(0, docWidth - viewportWidth, bodyWidth - viewportWidth);
            }"""
        )
    )


def run_audit(repo_root: Path) -> int:
    pages_to_test = [p for p in ("index.html", "cockpit.html") if (repo_root / p).exists()]
    if not pages_to_test:
        print(f"[ERROR] Neither index.html nor cockpit.html found in {repo_root}")
        return 1

    viewports = [
        ViewportSpec(name="desktop_1440x900", width=1440, height=900, is_mobile=False),
        ViewportSpec(name="mobile_390x844", width=390, height=844, is_mobile=True),
    ]
    themes: tuple[ThemeMode, ...] = ("dark", "light")

    screenshot_dir = repo_root / "audit" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    results: list[PageAuditResult] = []
    start_ts = time.perf_counter()

    with ThreadedStaticServer(repo_root) as server, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for vp in viewports:
                context = browser.new_context(
                    viewport={"width": vp.width, "height": vp.height},
                    is_mobile=vp.is_mobile,
                    has_touch=vp.is_mobile,
                    device_scale_factor=vp.device_scale_factor,
                )
                try:
                    for page_file in pages_to_test:
                        for theme in themes:
                            page = context.new_page()
                            console_errors: list[str] = []
                            page_errors: list[str] = []

                            page.on(
                                "console",
                                lambda msg: console_errors.append(msg.text)
                                if msg.type == "error"
                                else None,
                            )
                            page.on("pageerror", lambda err: page_errors.append(str(err)))

                            url = f"{server.base_url}/{page_file}"
                            page.goto(url, wait_until="domcontentloaded", timeout=15000)
                            page.wait_for_timeout(600)
                            apply_theme_and_settle(page, theme)

                            overflow_px = measure_horizontal_overflow(page)
                            stem = Path(page_file).stem
                            shot_path = screenshot_dir / f"{stem}__{vp.name}__{theme}.png"
                            page.screenshot(path=str(shot_path), full_page=True)

                            results.append(
                                PageAuditResult(
                                    page_name=page_file,
                                    viewport=vp.name,
                                    theme=theme,
                                    screenshot_path=shot_path,
                                    overflow_px=overflow_px,
                                    console_errors=console_errors,
                                    page_errors=page_errors,
                                )
                            )
                            page.close()
                finally:
                    context.close()
        finally:
            browser.close()

    elapsed = time.perf_counter() - start_ts
    failures = [r for r in results if not r.passed]

    print("=" * 84)
    print(f"PLAYWRIGHT VIEWPORT & THEME AUDIT ({elapsed:.2f}s) | Screenshots -> {screenshot_dir}")
    print("=" * 84)
    for res in results:
        status = "PASS" if res.passed else "FAIL"
        rel_shot = res.screenshot_path.relative_to(repo_root)
        print(
            f"[{status}] {res.page_name:<12} | {res.viewport:<16} | {res.theme:<5} | "
            f"Overflow: {res.overflow_px}px | ConsoleErr: {len(res.console_errors)} | "
            f"PageErr: {len(res.page_errors)} | {rel_shot}"
        )
        for err in res.console_errors:
            print(f"       -> [console.error] {err}")
        for err in res.page_errors:
            print(f"       -> [pageerror]     {err}")

    print("-" * 84)
    print(f"Total Checks: {len(results)} | Passed: {len(results) - len(failures)} | Failed: {len(failures)}")
    return 1 if failures else 0


def find_repo_root() -> Path:
    """Resolve repository root directory reliably from current script location."""
    for p in Path(__file__).resolve().parents:
        if (p / "index.html").exists() and (p / "results").exists():
            return p
    return Path(__file__).resolve().parent.parent.parent


if __name__ == "__main__":
    root = find_repo_root()
    sys.exit(run_audit(root))
