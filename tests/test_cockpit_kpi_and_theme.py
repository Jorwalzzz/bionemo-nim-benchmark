"""
Playwright regression tests for Phase 4:
- Multi-run cockpit KPI updates across presets & honest '—' on unseen static targets
- Light mode contrast & zero custom cursor / hero WebGL on welcome & cockpit
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

import functools
import http.server
import socketserver
import threading
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")

REPO_ROOT = Path(__file__).resolve().parent.parent


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


@pytest.fixture()
def static_site_url():
    handler = functools.partial(_QuietHandler, directory=str(REPO_ROOT))
    httpd = _Server(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_cockpit_multi_run_kpis_and_unseen_target_honesty(static_site_url: str) -> None:
    with playwright_sync.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script("localStorage.setItem('bionemo_guide_seen', 'true');")
        page.goto(f"{static_site_url}/cockpit.html", wait_until="domcontentloaded")
        page.wait_for_timeout(400)

        # Run 1: Preset 7RPZ (KRAS G12D)
        page.select_option("#targetSelect", "7RPZ")
        page.click("#runBtn")
        page.wait_for_function(
            "() => !document.getElementById('runBtn').disabled && document.getElementById('kpiAffinity').textContent !== '—' && document.getElementById('kpiAffinity').textContent !== '…'"
        )
        aff1 = page.locator("#kpiAffinity").inner_text().strip()
        qed1 = page.locator("#kpiQed").inner_text().strip()
        assert aff1 not in ("—", "…")

        # Run 2: Switch to Preset 2HYY (BCR-ABL1) -> KPIs must update cleanly
        page.select_option("#targetSelect", "2HYY")
        page.click("#runBtn")
        page.wait_for_function(
            "() => !document.getElementById('runBtn').disabled && document.getElementById('kpiAffinity').textContent !== '…'"
        )
        aff2 = page.locator("#kpiAffinity").inner_text().strip()
        qed2 = page.locator("#kpiQed").inner_text().strip()
        assert (aff2, qed2) != (aff1, qed1)
        assert "Run Autonomous Discovery" in page.locator("#runLabel").inner_text()

        # Run 3: Unseen RCSB PDB in static mode -> honest '—' (ZERO fabricated metrics!)
        page.click("#tabBtnRcsb")
        page.fill("#customTargetInput", "1XYZ")
        page.click("#runBtn")
        page.wait_for_function("() => !document.getElementById('runBtn').disabled")
        assert page.locator("#kpiAffinity").inner_text().strip() == "—"
        assert page.locator("#kpiQed").inner_text().strip() == "—"
        assert "Static GitHub Pages demo" in page.locator("#agentLog").inner_text()

        browser.close()


def test_light_mode_contrast_zero_custom_cursor_and_mobile_overflow(static_site_url: str) -> None:
    with playwright_sync.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Welcome page (index.html)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{static_site_url}/index.html", wait_until="domcontentloaded")
        page.wait_for_timeout(300)
        assert page.locator(".cursor-ring").count() == 0
        assert page.locator(".cursor-dot").count() == 0
        assert page.locator("#heroWebGLCanvas").count() == 0

        if page.evaluate("document.documentElement.getAttribute('data-theme')") != "light":
            page.click("#themeToggleBtn")
            page.wait_for_timeout(200)
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
        body_bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
        assert body_bg in ("rgb(248, 250, 252)", "rgb(246, 245, 241)")

        # 2. Cockpit page (cockpit.html) light mode + 390x844 zero overflow
        cpage = browser.new_page(viewport={"width": 390, "height": 844})
        cpage.add_init_script("localStorage.setItem('bionemo_guide_seen', 'true');")
        cpage.goto(f"{static_site_url}/cockpit.html", wait_until="domcontentloaded")
        cpage.wait_for_timeout(400)
        if cpage.evaluate("document.documentElement.getAttribute('data-theme')") != "light":
            cpage.click("#themeToggleBtn")
            cpage.wait_for_timeout(200)
        select_bg = cpage.evaluate("getComputedStyle(document.getElementById('targetSelect')).backgroundColor")
        assert select_bg == "rgb(255, 255, 255)"
        overflow = cpage.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 0

        browser.close()
