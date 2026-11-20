---
name: frontend-obsidian-lab
description: "Enforce the Bio-Precision Obsidian Lab design system for bionemo-nim-benchmark UI interfaces: #05070A canvas, #76F5A2 signal green, #5CE1FF bio-cyan, #FF8A4C CPU ember, Space Grotesk / Inter Tight / JetBrains Mono typography with tabular-nums, WCAG 2.2 AA contrast, zero-emoji inline SVG iconography, strictly relative paths (./...), and 1440x900 / 390x844 responsive viewport verification."
---

# Bio-Precision Obsidian Lab Design System

This skill governs all frontend interface development, styling, and visual audit procedures for `index.html`, `cockpit.html`, and custom UI components within the `bionemo-nim-benchmark` project.

## 1. Color Palette Tokens

The UI strictly adheres to the dark, high-contrast "Obsidian Lab" palette:

| Token Name | Hex Code | Semantic Role | Usage Guidance |
| :--- | :--- | :--- | :--- |
| **Canvas** | `#05070A` | Deepest Background | Primary `<body>` and full-viewport background |
| **Surface Dark** | `#0D1117` | Card & Panel Background | Benchmark cards, metric pods, container surfaces |
| **Surface Elevated** | `#161B22` | Header / Dropdown Surface | Sticky navbars, active tabs, modal dialogues |
| **Surface Alt** | `#101620` | Sub-panel / Data Table Rows | Alternating data rows, terminal consoles, code pods |
| **Border Slate** | `#30363D` | Default Structural Borders | Outer card borders, table dividers, card boundaries |
| **Signal Green** | `#76F5A2` | Bio / NIM / Measured Data | GPU inference speeds, passing tests, measured metrics |
| **Signal Green Dark** | `#10B981` | Accent Green / Badges | Solid measured badges, speedup highlights |
| **Bio Cyan** | `#5CE1FF` | Interactive / Structure / Active | 3D viewer toggles, active filter tabs, primary CTA links |
| **CPU Ember** | `#FF8A4C` | Baseline / Warning / Illustrative | CPU latency bars, projected figures, illustrative badges |
| **Text Primary** | `#F0F6FC` | High-contrast Heading / Ink | Card headings, headline numbers, bold labels |
| **Text Secondary** | `#8B949E` | Muted Subtext / Metadata | Unit labels, timestamps, benchmark descriptions |

## 2. Typography & Numeric Precision
- **Display & Headings:** `Space Grotesk`, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif. Used for headline titles, hero statistics, section headers.
- **Interface & Prose:** `Inter Tight`, `Inter`, -apple-system, BlinkMacSystemFont, sans-serif. Used for body text, button labels, documentation, tooltip copy.
- **Metrics, Latency & Code:** `JetBrains Mono`, ui-monospace, SFMono-Regular, Menlo, monospace.
- **Mandatory Tabular Alignment:** All numeric values, latencies, speedups, and table cells must enforce `font-variant-numeric: tabular-nums;` to prevent layout jitter during dynamic updates.

## 3. Strict Zero-Emoji Iconography Rule
- **No Emoji in UI Controls:** Never use Unicode emoji (e.g. ⚡, 🧬, 🚀, 🧪, 🔬) as interface icons or buttons.
- **Inline SVG Standards:** All icons must be clean, inline `<svg>` elements with:
  ```html
  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <!-- SVG paths -->
  </svg>
  ```
- **Accessibility:** Interactive icon buttons without adjacent text must include `aria-label="<Action Description>"` or an enclosed `<title>` tag. Decorative icons alongside text must have `aria-hidden="true"`.

## 4. Accessibility & WCAG 2.2 AA Compliance
- **Contrast Baseline:**
  - Normal text ($< 18\text{pt}$): Minimum contrast ratio of **$4.5:1$** against background.
  - Large text ($\ge 18\text{pt}$ or bold $\ge 14\text{pt}$): Minimum contrast ratio of **$3.0:1$**.
  - Interactive UI controls and focus rings: Minimum contrast ratio of **$3.0:1$**.
- **Form Controls:** Every `<input>`, `<select>`, and `<textarea>` must have an associated `<label for="id">` or explicit `aria-label`.
- **Keyboard Navigation:** All clickable elements must be focusable (`tabindex="0"`) with a visible focus outline: `focus-visible:ring-2 focus-visible:ring-[#5CE1FF] focus-visible:outline-none`.

## 5. GitHub Pages Path Discipline
- **Relative Path Mandate:** All asset references in HTML, CSS, and JS files must be relative:
  - Valid: `href="./css/cockpit.css"`, `src="./js/cockpit.js"`, `fetch("./results/benchmark_summary.json")`
  - Invalid: `href="/css/cockpit.css"`, `src="/js/cockpit.js"`, `fetch("/results/benchmark_summary.json")`
- **Subpath Safe:** The site is deployed at `https://jorwalzzz.github.io/bionemo-nim-benchmark/`. Root-relative paths point to the domain root and break immediately.

## 6. Viewport Validation Matrix
Before releasing UI changes, verify visual layouts across both standard test viewports:
- **Desktop Viewport:** `1440 × 900` px (Primary cockpit workstation layout)
- **Mobile Viewport:** `390 × 844` px (iPhone 14 / modern mobile layout)
- **Verification Command:**
  ```powershell
  python scripts/audit/audit_release.py
  ```
