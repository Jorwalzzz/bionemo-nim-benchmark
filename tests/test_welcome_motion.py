"""Playwright motion, LCP, and reduced-motion verification for index.html."""

from __future__ import annotations

import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def _start_static_server() -> tuple[ThreadingHTTPServer, int]:
    handler = partial(_QuietHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_welcome_motion_lcp_idle_and_reduced_motion() -> None:
    server, port = _start_static_server()
    base_url = f"http://127.0.0.1:{port}/index.html"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            console_errors: list[str] = []
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
            )

            page.goto(base_url, wait_until="domcontentloaded")
            h1_opacity = page.eval_on_selector(
                "#hero h1", "el => getComputedStyle(el).opacity"
            )
            assert h1_opacity == "1", f"Hero H1 must be immediately visible for LCP, got {h1_opacity}"

            page.wait_for_load_state("networkidle")
            time.sleep(2.0)

            running_infinite = page.evaluate(
                """() => {
                    return document.getAnimations()
                        .filter(a => a.playState === 'running' && a.effect && a.effect.getTiming().iterations === Infinity)
                        .map(a => a.effect.target ? a.effect.target.className : 'unknown');
                }"""
            )
            assert running_infinite == [], f"Expected zero idle infinite animations at y=0, found {running_infinite}"

            # Synchronous calculator slider update check
            before_txt = page.locator("#calc-count-display").inner_text()
            page.locator("#calc-slider").fill("80")
            page.locator("#calc-slider").dispatch_event("input")
            after_txt = page.locator("#calc-count-display").inner_text()
            assert after_txt != before_txt, "Slider input did not update #calc-count-display synchronously"

            # Reduced motion check
            page.emulate_media(reduced_motion="reduce")
            page.goto(base_url, wait_until="networkidle")
            reduced_h1 = page.eval_on_selector(
                "#hero h1", "el => getComputedStyle(el).opacity"
            )
            assert reduced_h1 == "1"
            assert console_errors == [], f"Console errors: {console_errors}"
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
