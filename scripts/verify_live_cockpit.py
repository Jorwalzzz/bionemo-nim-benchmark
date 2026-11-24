"""
Live Playwright Verification against GitHub Pages Deployment.
Target: https://jorwalzzz.github.io/bionemo-nim-benchmark/cockpit.html
"""

from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

LIVE_URL = "https://jorwalzzz.github.io/bionemo-nim-benchmark/cockpit.html"

def verify_live():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print(f"Navigating to {LIVE_URL}...")
        resp = page.goto(LIVE_URL, wait_until="networkidle")

        # 1. HTTP 200 & Asset Version Tag
        status = resp.status if resp else 0
        html = page.content()
        has_v = "?v=20261121" in html
        results["HTTP_200"] = status == 200
        results["ASSET_VERSION_TAG"] = has_v
        print(f"HTTP Status: {status}, Version Tag present: {has_v}")

        # 2. Initial KPI cards render '—' and empty state visible
        kpi_aff = page.locator("#kpiAffinity").inner_text().strip()
        kpi_qed = page.locator("#kpiQed").inner_text().strip()
        kpi_sc = page.locator("#kpiScreened").inner_text().strip()
        kpi_par = page.locator("#kpiPareto").inner_text().strip()

        kpi_clean = (kpi_aff == "—" and kpi_qed == "—" and kpi_sc == "—" and kpi_par == "—")
        results["CLEAN_IDLE_KPIS"] = kpi_clean
        print(f"KPIs idle: aff={kpi_aff}, qed={kpi_qed}, screened={kpi_sc}, pareto={kpi_par} -> {kpi_clean}")

        # 3. Offline demo provenance banner visible
        prov_text = page.locator("#provenanceBadge").inner_text()
        has_prov = "OFFLINE DEMO" in prov_text and "SIMULATION" in prov_text
        results["PROVENANCE_BANNER"] = has_prov
        print(f"Provenance banner: '{prov_text}' -> {has_prov}")

        # 4. Zero console errors on load
        results["ZERO_CONSOLE_ERRORS_LOAD"] = len(console_errors) == 0
        print(f"Console errors on load: {console_errors}")

        # 5. Static mode pill visible and Sign In button hidden on remote origin
        static_pill = page.locator("#staticDemoPill")
        auth_hud = page.locator("#authHudContainer")
        is_static_pill_visible = static_pill.is_visible()
        is_auth_hud_hidden = not auth_hud.is_visible()
        results["STATIC_HEADER_UX"] = is_static_pill_visible and is_auth_hud_hidden
        print(f"Static pill visible: {is_static_pill_visible}, Auth HUD hidden: {is_auth_hud_hidden}")

        # 6. Select BRAF V600E (4MNE) and run discovery
        print("Selecting 4MNE...")
        page.select_option("#targetSelect", "4MNE")
        page.wait_for_timeout(300)

        target_res = page.locator("#targetRes").inner_text().strip()
        print(f"4MNE Resolution displayed: {target_res}")
        results["4MNE_RESOLUTION_285"] = "2.85" in target_res

        page.click("#runBtn")
        page.wait_for_selector("#runBtn:not([disabled])", timeout=20000)
        page.wait_for_timeout(500)

        # 7. Verify leads generated for 4MNE (BRAF-specific, zero MRTX1133)
        leads_text = page.locator("#leadsContainer").inner_text()
        log_text = page.locator("#agentLog").inner_text()
        full_text = f"{leads_text}\n{log_text}"

        has_vemurafenib = "VEMURAFENIB-SIM-01" in leads_text
        has_simulated_badge = "SIMULATED" in leads_text
        has_no_kras_leak = ("MRTX1133" not in full_text) and ("Thr790" not in full_text)

        results["BRAF_LEADS_GENERATED"] = has_vemurafenib and has_simulated_badge
        results["ZERO_KRAS_LEAK"] = has_no_kras_leak
        print(f"Vemurafenib lead generated: {has_vemurafenib}, Simulated badge: {has_simulated_badge}, Zero KRAS leak: {has_no_kras_leak}")

        # Final check on console errors after run
        results["ZERO_CONSOLE_ERRORS_FINAL"] = len(console_errors) == 0
        print(f"Total console errors after full interaction: {console_errors}")

        browser.close()

    print("\n--- FINAL TEST RESULTS ---")
    all_passed = True
    for k, v in results.items():
        status_str = "PASS" if v else "FAIL"
        print(f"{k}: {status_str}")
        if not v:
            all_passed = False

    if not all_passed:
        sys.exit(1)
    print("\nALL LIVE CHECKS PASSED!")

if __name__ == "__main__":
    verify_live()
