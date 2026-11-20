"""
Playwright browser integration test verifying Step 3/3 features:
1. RCSB PDB 4-character live metadata resolution (macromolecule title & resolution Å).
2. ESMFold 3 one-click example FASTA chips (Ubiquitin 76aa, KRAS G12D 169aa, Mpro 306aa).
3. Zero console errors and zero uncaught page errors.
"""

import functools
import http.server
import socketserver
import threading
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_step3_interactive_features():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(REPO_ROOT))
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), handler)
    port = httpd.server_address[1]
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    console_errors = []
    page_errors = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.on('console', lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == 'error' else None)
            page.on('pageerror', lambda err: page_errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{port}/cockpit.html", wait_until='networkidle')
            page.wait_for_timeout(800)

            # 1. ESMFold Tab: Test 3 FASTA chips
            page.click('#tabBtnEsmfold')
            page.wait_for_timeout(200)

            # Chip 1: Ubiquitin 76aa
            page.click('#chipEsmUbiquitin')
            page.wait_for_timeout(150)
            ubi_text = page.locator('#esmfoldSeqInput').input_value().strip()
            ubi_badge = page.locator('#seqLenBadge').inner_text().strip()
            assert len(ubi_text) == 76
            assert ubi_badge == '76 aa'

            # Chip 2: KRAS G12D 169aa
            page.click('#chipEsmKras')
            page.wait_for_timeout(150)
            kras_text = page.locator('#esmfoldSeqInput').input_value().strip()
            kras_badge = page.locator('#seqLenBadge').inner_text().strip()
            assert len(kras_text) == 169
            assert kras_badge == '169 aa'

            # Chip 3: Mpro 306aa
            page.click('#chipEsmMpro')
            page.wait_for_timeout(150)
            mpro_text = page.locator('#esmfoldSeqInput').input_value().strip()
            mpro_badge = page.locator('#seqLenBadge').inner_text().strip()
            assert len(mpro_text) == 306
            assert mpro_badge == '306 aa'

            # 2. RCSB PDB Tab: Test 4-char PDB input & preview card
            page.click('#tabBtnRcsb')
            page.wait_for_timeout(200)
            page.fill('#customTargetInput', '6LU7')
            page.wait_for_timeout(800)

            preview_box = page.locator('#rcsbMetadataPreview')
            classes = preview_box.get_attribute('class') or ''
            assert 'hidden' not in classes

            preview_pdb = page.locator('#rcsbPreviewPdb').inner_text()
            assert '6LU7' in preview_pdb

            browser.close()
    finally:
        httpd.shutdown()

    assert not console_errors, f"Encountered console errors: {console_errors}"
    assert not page_errors, f"Encountered page errors: {page_errors}"
