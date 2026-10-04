#!/usr/bin/env python3
"""
Antigravity Ultimate Encyclopedia Generator
Compiles an exhaustive, multi-chapter reference manual into both mobile-responsive HTML and publication-grade PDF.
"""

import os
import subprocess
import shutil

html_path = os.path.abspath("ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.html")
pdf_path = os.path.abspath("ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.pdf")

content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>The Antigravity IDE Master Encyclopedia: 100% Potential Decoded</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --surface: #111827;
      --surface-elevated: #1f2937;
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(56, 189, 248, 0.3);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.12);
      --green: #10b981;
      --green-glow: rgba(16, 185, 129, 0.12);
      --purple: #a855f7;
      --purple-glow: rgba(168, 85, 247, 0.12);
      --amber: #f59e0b;
      --amber-glow: rgba(245, 158, 11, 0.12);
      --rose: #f43f5e;
      --rose-glow: rgba(244, 63, 94, 0.12);
    }
    @page {
      margin: 12mm;
      size: A4 portrait;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      line-height: 1.6;
      padding: 24px 16px 80px;
      -webkit-font-smoothing: antialiased;
      max-width: 900px;
      margin: 0 auto;
    }

    header {
      text-align: center;
      padding: 30px 10px 24px;
      border-bottom: 2px solid var(--border);
      margin-bottom: 30px;
    }
    .badge-hero {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      padding: 6px 14px;
      border-radius: 999px;
      background: var(--primary-glow);
      color: var(--primary);
      border: 1px solid var(--border-accent);
      margin-bottom: 14px;
    }
    h1 {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.25;
      margin-bottom: 8px;
    }
    .subtitle {
      font-size: 14px;
      color: var(--text-muted);
      max-width: 650px;
      margin: 0 auto;
    }

    /* TOC */
    .toc {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 35px;
    }
    .toc-title {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--primary);
      margin-bottom: 12px;
    }
    .toc-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
      font-size: 13.5px;
    }
    @media(min-width: 600px) { .toc-grid { grid-template-columns: 1fr 1fr; } }
    .toc-grid a {
      color: #cbd5e1;
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .toc-grid a:hover { color: var(--primary); }

    /* Chapter Headers */
    .chapter-header {
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.12), transparent);
      border-left: 5px solid var(--primary);
      padding: 14px 18px;
      margin: 45px 0 20px;
      border-radius: 0 12px 12px 0;
      page-break-after: avoid;
    }
    .chapter-num {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--primary);
      margin-bottom: 2px;
    }
    .chapter-title {
      font-size: 19px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #fff;
    }

    h3 {
      font-size: 16px;
      font-weight: 700;
      color: #e2e8f0;
      margin: 24px 0 10px;
      page-break-after: avoid;
    }
    p {
      font-size: 14px;
      color: #cbd5e1;
      margin-bottom: 12px;
    }

    /* Cards */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 14px;
      page-break-inside: avoid;
    }
    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 6px;
    }
    .card-title {
      font-size: 15px;
      font-weight: 700;
      color: #fff;
    }
    .badge {
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .badge.blue { background: var(--primary-glow); color: var(--primary); border: 1px solid var(--border-accent); }
    .badge.green { background: var(--green-glow); color: var(--green); border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge.purple { background: var(--purple-glow); color: var(--purple); border: 1px solid rgba(168, 85, 247, 0.3); }
    .badge.amber { background: var(--amber-glow); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge.rose { background: var(--rose-glow); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }

    .card-desc {
      font-size: 13.5px;
      color: #cbd5e1;
      margin-bottom: 10px;
    }
    .card-meta {
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 10px;
      margin-top: 10px;
      font-size: 12.5px;
      color: var(--text-muted);
    }
    .card-meta strong { color: #f1f5f9; }

    /* Keyboards & Code */
    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
      color: #38bdf8;
      background: rgba(15, 23, 42, 0.85);
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    kbd {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 4px;
      background: #1e293b;
      color: #f8fafc;
      border: 1px solid #334155;
    }

    /* Callout */
    .callout {
      background: rgba(56, 189, 248, 0.08);
      border-left: 4px solid var(--primary);
      border-radius: 0 10px 10px 0;
      padding: 14px 16px;
      margin: 16px 0;
      font-size: 13.5px;
    }
    .callout.amber { background: var(--amber-glow); border-left-color: var(--amber); }
    .callout.rose { background: var(--rose-glow); border-left-color: var(--rose); }

    /* Tier Styling */
    .tier-rookie { border-left: 4px solid var(--green); }
    .tier-pro { border-left: 4px solid var(--amber); }
    .tier-master { border-left: 4px solid var(--rose); }

    /* Grid layout for skills */
    .skills-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }
    @media(min-width: 650px) { .skills-grid { grid-template-columns: 1fr 1fr; } }

    footer {
      text-align: center;
      margin-top: 60px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <header>
    <div class="badge-hero">Definitive 100% Operating Manual</div>
    <h1>The Antigravity IDE Master Encyclopedia</h1>
    <p class="subtitle">The complete exhaustive reference: Every surface, model, modality, tool, skill, and 100% potential execution blueprint.</p>
  </header>

  <!-- TABLE OF CONTENTS -->
  <div class="toc">
    <div class="toc-title">Volume Sitemap & Index</div>
    <div class="toc-grid">
      <a href="#ch1">📖 1. The 3 Core AI Modalities</a>
      <a href="#ch2">🤖 2. The 7 Models & Reasoning Tiers</a>
      <a href="#ch3">⚡ 3. Chat Canvas, @ Mentions & Slashes</a>
      <a href="#ch4">🛡️ 4. Settings, Policies & Sandboxes</a>
      <a href="#ch5">🚀 5. Subagents & Background Fleet</a>
      <a href="#ch6">🛠️ 6. Core Native Tools & I/O Engine</a>
      <a href="#ch7">🔌 7. Integrated MCP Server Suites</a>
      <a href="#ch8">🧬 8. Complete 57-Skills Encyclopedia</a>
      <a href="#ch9">🎯 9. The 3 User Tiers: 0% to 100%</a>
      <a href="#ch10">💰 10. Token Economics & Audit Analytics</a>
    </div>
  </div>

  <!-- CHAPTER 1 -->
  <div class="chapter-header" id="ch1">
    <div class="chapter-num">Chapter 1</div>
    <div class="chapter-title">The 3 Core AI Modalities in Antigravity IDE</div>
  </div>
  <p>Antigravity is not a simple chat sidebar slapped onto an editor. It is an AI-first development platform built around 3 distinct interaction modes tailored to task scope:</p>

  <div class="card">
    <div class="card-top">
      <span class="card-title">A. Passive Modality: Antigravity Tab</span>
      <span class="badge green">Next-Intent Prediction</span>
    </div>
    <div class="card-desc">
      A real-time next-intent prediction engine running silently on every keystroke. Unlike standard single-line autocompletes, Antigravity Tab understands surrounding open tabs, terminal outputs, recent diffs, and clipboard context.
    </div>
    <div class="card-meta">
      • <strong>Tab to Jump:</strong> Anticipates where your cursor needs to go next (e.g., closing braces, next function argument, or calling code); press <kbd>Tab</kbd> to jump across lines instantly.<br>
      • <strong>Tab to Import:</strong> When you reference an unimported symbol or package, pressing <kbd>Tab</kbd> automatically adds the clean import at the top of the file without disrupting your line position.<br>
      • <strong>Supercomplete:</strong> Displays floating multi-line refactorings and deletions right in your code canvas.<br>
      • <strong>Keystroke Controls:</strong> <kbd>Tab</kbd> accepts full suggestion, <kbd>Esc</kbd> cancels, and <kbd>Ctrl</kbd>+<kbd>→</kbd> (or <kbd>Cmd</kbd>+<kbd>→</kbd>) accepts word-by-word.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">B. Instructive Modality: Inline Command (<kbd>Ctrl</kbd>+<kbd>I</kbd> / <kbd>Cmd</kbd>+<kbd>I</kbd>)</span>
      <span class="badge blue">In-Editor Surgical Edits</span>
    </div>
    <div class="card-desc">
      Designed for targeted in-place code modification without switching mental context to the chat sidebar.
    </div>
    <div class="card-meta">
      • <strong>Targeted Refactoring:</strong> Highlight a specific code block, hit <kbd>Ctrl</kbd>+<kbd>I</kbd>, and prompt: <em>"Convert to async/await"</em> or <em>"Vectorize with NumPy"</em>. Only the highlighted lines are touched.<br>
      • <strong>Net-New Code Generation:</strong> Trigger <kbd>Ctrl</kbd>+<kbd>I</kbd> on an empty line with a descriptive prompt to generate boilerplate, classes, or test cases directly at the cursor.<br>
      • <strong>Instant Documentation:</strong> Highlight any function and trigger <kbd>Ctrl</kbd>+<kbd>I</kbd> with <em>"Add type annotations and Sphinx docstrings"</em>.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">C. Collaborative Modality: Sidebar Chat & Agent Mode</span>
      <span class="badge purple">Full-Stack Pair Programmer</span>
    </div>
    <div class="card-desc">
      The full agentic pair programmer capable of multi-step autonomous reasoning, executing shell commands, reading file trees, diagnosing failures, and managing MCP tools.
    </div>
    <div class="card-meta">
      • <strong>Inline Code Lenses:</strong> Action triggers rendered directly above classes and functions (<em>"Explain"</em>, <em>"Write Unit Tests"</em>, <em>"Refactor"</em>).<br>
      • <strong>Diagnostic Auto-Fix:</strong> Click on compiler errors, lint squiggly lines, or Problems pane entries to invoke the agent directly to analyze and heal the issue.<br>
      • <strong>Visual Diff Overlays:</strong> Review inline red/green diffs directly inside your editor canvas before committing changes.
    </div>
  </div>

  <!-- CHAPTER 2 -->
  <div class="chapter-header" id="ch2">
    <div class="chapter-num">Chapter 2</div>
    <div class="chapter-title">The 7 Exact Models & Reasoning Tiers</div>
  </div>
  <p>Antigravity exposes 7 state-of-the-art models in your dropdown menu. Matching the model to the exact problem is the single greatest lever for execution quality and token savings:</p>

  <div class="card">
    <div class="card-top">
      <span class="card-title">1. Gemini 3.8 Flash (Medium / Low)</span>
      <span class="badge green">⚡ Ultra Fast Daily Driver</span>
    </div>
    <div class="card-desc"><strong>The Daily Workhorse (80% of all programming tasks).</strong> Sub-second latency, highest MCP tool execution throughput, lowest token burn, and massive context capacity.</div>
    <div class="card-meta">
      <strong>Best For:</strong> Daily coding, running pytest suites, CLI benchmarks, high-volume file editing.<br>
      <strong>Avoid For:</strong> Abstract mathematical architecture with 15+ circular dependencies.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">2. Claude Sonnet 5.5 (Medium)</span>
      <span class="badge amber">🎨 Gold Standard UI & Clean Code</span>
    </div>
    <div class="card-desc"><strong>Unmatched frontend design aesthetics and idiomatic code taste.</strong> Produces stunning, modern web apps (CSS/JS) and pristine, typed Python refactors.</div>
    <div class="meta">
      <strong>Best For:</strong> BioNeMo Cockpit UI, modern CSS/JS interfaces, clean architecture.<br>
      <strong>Avoid For:</strong> Trivial shell loops or repetitive regex transforms.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">3. Claude Opus 5.5 (Medium)</span>
      <span class="badge rose">🧠 Maximum Cognitive Depth (S-Tier)</span>
    </div>
    <div class="card-desc"><strong>Supreme architectural and mathematical reasoning.</strong> Solves novel algorithmic challenges, high-stakes system redesigns, and hard bug autopsies.</div>
    <div class="card-meta">
      <strong>Best For:</strong> Designing core algorithms from scratch, multi-module pipeline graphs.<br>
      <strong>Avoid For:</strong> Fast back-and-forth chat or budget-limited sessions.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">4. Gemini 3.1 Pro (Low)</span>
      <span class="badge purple">🧠 Deliberate Logic & Concurrency</span>
    </div>
    <div class="card-desc"><strong>Deliberate multi-hop reasoning.</strong> Traces complex concurrency bugs, race conditions, memory leaks, and interface contracts.</div>
    <div class="card-meta">
      <strong>Best For:</strong> Diagnosing subtle pipeline crashes, security audits, schema boundaries.<br>
      <strong>Avoid For:</strong> Simple one-line edits or trivial renames.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">5. Gemini 3.7 Flash & 6. Gemini 3.6 Flash</span>
      <span class="badge blue">⚡ Proven Stability & Batch</span>
    </div>
    <div class="card-desc">Rock-solid schema following and high-throughput batch script execution without experimental API drift.</div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">7. GPT-OSS 120B (Medium)</span>
      <span class="badge amber">⚖️ Open-Weight Second Opinion</span>
    </div>
    <div class="card-desc">Neutral open-weights architecture for unbiased code reviews and cross-model validation.</div>
  </div>

  <div class="callout amber">
    <strong>Reasoning Modifiers Decoded:</strong><br>
    • <strong><code>Low</code> Reasoning:</strong> Bypasses internal scratchpad thinking. Responds immediately. Saves maximum tokens and execution time.<br>
    • <strong><code>Medium</code> Reasoning:</strong> Allocates hidden reasoning tokens for internal chain-of-thought analysis before outputting code. Prevents logic regressions in complex multi-step diffs.
  </div>

  <!-- CHAPTER 3 -->
  <div class="chapter-header" id="ch3">
    <div class="chapter-num">Chapter 3</div>
    <div class="chapter-title">Chat Canvas, @ Mentions & Slash Commands</div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">The Power of @ Mentions</span>
      <span class="badge blue">Targeted Context</span>
    </div>
    <div class="card-desc">Type <code>@</code> in the chat input to inject rich context directly without manual copy-pasting:</div>
    <div class="card-meta">
      • <code>@Files & Folders</code>: Attaches file paths so the agent reads line-bounded slices instead of burning tokens.<br>
      • <code>@Previous Conversations</code>: Bridges context from earlier sessions without starting from scratch.<br>
      • <code>@Terminal Sessions</code>: Injects terminal output directly into prompt context.<br>
      • <code>@Rules</code>: Enforces specific coding guidelines on demand.<br>
      • <code>@MCP Tools</code>: Explicitly targets a specific MCP tool suite.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">Slash Commands (Built-In Agent Automations)</span>
      <span class="badge green">Workflows</span>
    </div>
    <div class="card-meta">
      • <code>/plan</code>: Interactive, phased blueprint before touching any code. Avoids circular work.<br>
      • <code>/goal</code>: Autonomous endurance mode; runs continuous execution loops until finished.<br>
      • <code>/grill-me</code>: Interviews you like a Staff Engineer to tease out edge cases and assumptions.<br>
      • <code>/learn</code>: Saves corrected rules and workflows into permanent memory across sessions.<br>
      • <code>/schedule</code>: Configures one-shot timers or recurring cron triggers.
    </div>
  </div>

  <!-- CHAPTER 4 -->
  <div class="chapter-header" id="ch4">
    <div class="chapter-num">Chapter 4</div>
    <div class="chapter-title">Settings, Policies & Security Sandboxes</div>
  </div>
  <p>Antigravity features granular enterprise security policies configured globally in Settings or locally in <code>.agents/</code>:</p>

  <div class="card">
    <div class="card-desc">
      • <strong>Tool Execution Policy:</strong> Choose between <code>always-proceed</code> (full autonomous speed), <code>request-review</code> (asks before every terminal command), or <code>proceed-in-sandbox</code>.<br>
      • <strong>Terminal Sandbox:</strong> Isolates shell commands in a container to prevent accidental system modifications.<br>
      • <strong>Workspace Root Boundary:</strong> Enforces that all file reads and writes remain within project boundaries unless explicitly permitted.<br>
      • <strong>Accidental Data Loss Prevention:</strong> Automatic gate blocking destructive database operations (<code>DROP TABLE</code>, <code>TRUNCATE</code>) or recursive disk wipes without explicit user confirmation.
    </div>
  </div>

  <!-- CHAPTER 5 -->
  <div class="chapter-header" id="ch5">
    <div class="chapter-num">Chapter 5</div>
    <div class="chapter-title">Subagents & Background Fleet Execution</div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">Reactive Wakeup vs Busy Polling</span>
      <span class="badge purple">Token Economics</span>
    </div>
    <div class="card-desc">
      Antigravity runs an event-driven agent loop. When long-running shell commands, benchmarks, or builds are dispatched, the agent halts its turn and enters sleep state. The platform wakes the agent up automatically upon task exit, saving thousands of tokens that would otherwise be wasted on empty status-polling loops.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">Autonomous Browser Subagent (`browser_subagent`)</span>
      <span class="badge blue">E2E Visual QA</span>
    </div>
    <div class="card-desc">
      Spawns a specialized browser worker that launches headless Chromium, navigates local servers, clicks DOM elements, types into forms, tests viewports, audits accessibility, and records WebP session videos for visual proof.
    </div>
  </div>

  <!-- CHAPTER 6 -->
  <div class="chapter-header" id="ch6">
    <div class="chapter-num">Chapter 6</div>
    <div class="chapter-title">Core Native Tools & I/O Engine</div>
  </div>

  <div class="card">
    <div class="card-meta">
      • <code>view_file</code>: Reads text, images, PDFs, or audio with precise line slices (<code>StartLine</code>/<code>EndLine</code>) to protect context.<br>
      • <code>replace_file_content</code>: Surgically updates a single contiguous block of code without touching the rest of the file.<br>
      • <code>multi_replace_file_content</code>: Performs multiple non-contiguous edits across a file in a single atomic transaction.<br>
      • <code>write_to_file</code>: Creates new files or overwrites existing files.<br>
      • <code>grep_search</code>: High-speed ripgrep search matching exact strings or regex patterns across the codebase.<br>
      • <code>list_dir</code>: Recursively lists directory contents and file sizes.<br>
      • <code>run_command</code>: Executes PowerShell commands in the user's workspace.<br>
      • <code>manage_task</code>: Controls background processes (<code>list</code>, <code>kill</code>, <code>status</code>, <code>send_input</code>).<br>
      • <code>schedule</code>: Configures asynchronous timers or cron jobs.
    </div>
  </div>

  <!-- CHAPTER 7 -->
  <div class="chapter-header" id="ch7">
    <div class="chapter-num">Chapter 7</div>
    <div class="chapter-title">Integrated MCP Server Suites</div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">🧬 NVIDIA BioNeMo & NIM Suite (`bionemo-tools`)</span>
      <span class="badge green">BioNeMo</span>
    </div>
    <div class="card-desc">
      • <code>bionemo_validate_sequence</code>: Validates protein sequences against the 20 canonical IUPAC amino acid residues.<br>
      • <code>bionemo_sanitize_smiles</code>: Performs RDKit sanitization, valency checking, and aromaticity verification.<br>
      • <code>bionemo_query_esm2_embedding</code>: Queries ESM-2 protein language models for residue or sequence representations.<br>
      • <code>bionemo_query_esmfold</code>: Predicts 3D atomic coordinates (.pdb) from raw sequences with pLDDT scoring.<br>
      • <code>bionemo_query_diffdock</code>: Generative molecular docking of small molecules to target protein pockets.<br>
      • <code>bionemo_fetch_rcsb_pdb</code>: Fetches and strips water/heteroatoms from experimental crystal structures.<br>
      • <code>bionemo_compare_known_inhibitors</code>: Computes Tanimoto similarity and Lipinski properties against reference drugs.<br>
      • <code>bionemo_run_benchmark</code>: Profiles GPU NIM latency, throughput, and generates 300 DPI publication plots.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">🐙 GitHub MCP Server (`github-mcp-server`)</span>
      <span class="badge purple">Git Automation</span>
    </div>
    <div class="card-desc">
      • Repositories: <code>create_repository</code>, <code>fork_repository</code>, <code>search_repositories</code>.<br>
      • Version Control: <code>create_branch</code>, <code>list_commits</code>, <code>create_or_update_file</code>, <code>push_files</code>.<br>
      • Collaboration: <code>create_pull_request</code>, <code>get_pull_request</code>, <code>merge_pull_request</code>, <code>create_issue</code>, <code>list_issues</code>.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">🎨 Stitch UI & Design System (`StitchMCP`)</span>
      <span class="badge amber">UI Generation</span>
    </div>
    <div class="card-desc">
      • <code>create_project</code>, <code>get_project</code>, <code>generate_screen_from_text</code>, <code>edit_screens</code>, <code>generate_variants</code>, <code>create_design_system</code>, <code>apply_design_system</code>.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">🌐 Chrome DevTools MCP (`chrome-devtools-mcp`)</span>
      <span class="badge blue">Browser Automation</span>
    </div>
    <div class="card-desc">
      • <code>new_page</code>, <code>navigate_page</code>, <code>click</code>, <code>type_text</code>, <code>fill_form</code>, <code>take_screenshot</code>, <code>evaluate_script</code>, <code>lighthouse_audit</code>, <code>performance_start_trace</code>, <code>list_console_messages</code>.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">🔍 Perplexity Research (`perplexity-ask`)</span>
      <span class="badge rose">Literature</span>
    </div>
    <div class="card-desc">
      • <code>perplexity_ask</code>: Real-time academic literature synthesis, drug target discovery, and scientific fact-checking with cited URLs.
    </div>
  </div>

  <!-- CHAPTER 8 -->
  <div class="chapter-header" id="ch8">
    <div class="chapter-num">Chapter 8</div>
    <div class="chapter-title">Complete 57-Skills Encyclopedia</div>
  </div>
  <p>Your environment is loaded with 57 specialized skill modules across biology, chemistry, browser debugging, and agent governance. Here is every skill indexed with its exact purpose:</p>

  <div class="skills-grid">
    <div class="card">
      <div class="card-title">alphafold_database_fetch_and_analyze</div>
      <div class="card-desc">Fetches AlphaFold predicted structures by UniProt ID, extracts pLDDT metrics, domain boundaries, and disorder scores.</div>
    </div>
    <div class="card">
      <div class="card-title">alphagenome_atlas_website_links</div>
      <div class="card-desc">Constructs deep links for the AlphaGenome Atlas, locus views, and candidate summary tables.</div>
    </div>
    <div class="card">
      <div class="card-title">alphagenome_single_variant_analysis</div>
      <div class="card-desc">Analyzes non-coding variant effects on gene expression (RNA-seq), chromatin accessibility, and transcription factors.</div>
    </div>
    <div class="card">
      <div class="card-title">alphagenome_variant_impact_score</div>
      <div class="card-desc">Computes AlphaGenome Variant Impact (AVI) scores and performs saturation mutagenesis window scans.</div>
    </div>
    <div class="card">
      <div class="card-title">bionemo-benchmark-profiler</div>
      <div class="card-desc">Benchmarks GPU NIM token throughput, latency scaling, P95/P99 distributions, and renders 300 DPI publication plots.</div>
    </div>
    <div class="card">
      <div class="card-title">bionemo-esmfold-generation</div>
      <div class="card-desc">Predicts 3D atomic coordinates from raw protein sequences via ESMFold NIM with per-residue pLDDT evaluation.</div>
    </div>
    <div class="card">
      <div class="card-title">bionemo-nim-inference</div>
      <div class="card-desc">Interfaces with NVIDIA BioNeMo hosted Cloud APIs and local GPU Docker containers with rate-limiting and mock testing.</div>
    </div>
    <div class="card">
      <div class="card-title">cheminformatics-rdkit-bionemo</div>
      <div class="card-desc">Small molecule processing, SMILES sanitization, valency verification, 3D conformers, and Lipinski Rule of 5 descriptors.</div>
    </div>
    <div class="card">
      <div class="card-title">chembl_database</div>
      <div class="card-desc">Queries ChEMBL for bioactive molecules, drug targets, IC50/Ki values, approved drugs, and chemical structures.</div>
    </div>
    <div class="card">
      <div class="card-title">clinical_trials_database</div>
      <div class="card-desc">Queries ClinicalTrials.gov APIv2 by condition, drug, phase, sponsor, and eligibility criteria.</div>
    </div>
    <div class="card">
      <div class="card-title">clinvar_database</div>
      <div class="card-desc">Retrieves clinical significance and pathogenicity classifications (Pathogenic, Benign, VUS) for genomic variants.</div>
    </div>
    <div class="card">
      <div class="card-title">dbsnp_database</div>
      <div class="card-desc">Maps rsIDs, genomic coordinates, and HGVS strings in NCBI dbSNP for human genetic variants.</div>
    </div>
    <div class="card">
      <div class="card-title">embl_ebi_ols</div>
      <div class="card-desc">Searches the EMBL-EBI Ontology Lookup Service across 250+ ontologies (GO, DOID, HP) for hierarchies and terms.</div>
    </div>
    <div class="card">
      <div class="card-title">encode_ccres_database</div>
      <div class="card-desc">Queries the ENCODE Registry of cis-Regulatory Elements via SCREEN GraphQL and ENCODE REST APIs.</div>
    </div>
    <div class="card">
      <div class="card-title">ensembl_database</div>
      <div class="card-desc">Resolves gene, transcript, and protein IDs, fetches genomic sequences, and retrieves VEP consequence predictions.</div>
    </div>
    <div class="card">
      <div class="card-title">foldseek_structural_search</div>
      <div class="card-desc">Performs 3D structural searches of PDB/mmCIF coordinate files against PDB, AlphaFold, and CATH databases.</div>
    </div>
    <div class="card">
      <div class="card-title">gnomad_database</div>
      <div class="card-desc">Queries gnomAD for allele frequencies, loss-of-function intolerance (pLI, LOEUF), and constraint metrics.</div>
    </div>
    <div class="card">
      <div class="card-title">gtex_database</div>
      <div class="card-desc">Retrieves RNA expression data and eQTL associations across 54 human non-diseased tissue sites.</div>
    </div>
    <div class="card">
      <div class="card-title">human_protein_atlas_database</div>
      <div class="card-desc">Retrieves semi-quantitative protein expression and subcellular spatial localization data from HPA.</div>
    </div>
    <div class="card">
      <div class="card-title">interpro_database</div>
      <div class="card-desc">Annotates protein domains, families, and functional sites combining 14 databases (Pfam, CDD, InterPro-N).</div>
    </div>
    <div class="card">
      <div class="card-title">jaspar_database</div>
      <div class="card-desc">Retrieves Position Weight Matrices (PWMs) and binding profiles for transcription factors.</div>
    </div>
    <div class="card">
      <div class="card-title">literature_search_arxiv / biorxiv / europepmc / openalex</div>
      <div class="card-desc">Full-text academic literature searches, DOI resolution, preprint retrieval, and citation bibliometrics.</div>
    </div>
    <div class="card">
      <div class="card-title">macromolecular-pdb-prep</div>
      <div class="card-desc">Cleans macromolecular structures, strips heteroatoms/waters, extracts IUPAC sequences, and prepares receptors for DiffDock.</div>
    </div>
    <div class="card">
      <div class="card-title">ncbi_sequence_fetch</div>
      <div class="card-desc">Retrieves protein and nucleotide sequences from NCBI databases via E-utilities.</div>
    </div>
    <div class="card">
      <div class="card-title">openfda_database</div>
      <div class="card-desc">Queries FDA adverse event reports, recalls, labeling, approvals, and drug safety data across 28 endpoints.</div>
    </div>
    <div class="card">
      <div class="card-title">opentargets_database</div>
      <div class="card-desc">Queries Open Targets Platform for target-disease associations, tractability, and clinical evidence.</div>
    </div>
    <div class="card">
      <div class="card-title">pdb_database</div>
      <div class="card-desc">Searches and downloads experimentally determined 3D structures from RCSB PDB with experimental metadata.</div>
    </div>
    <div class="card">
      <div class="card-title">pubchem_database & pubmed_database</div>
      <div class="card-desc">Cheminformatics property lookups, compound similarity, bioactivity assays, and PubMed literature indexing.</div>
    </div>
    <div class="card">
      <div class="card-title">pymol</div>
      <div class="card-desc">Automates PyMOL rendering, structural superposition, active site contact measurement, and pLDDT color-coding.</div>
    </div>
    <div class="card">
      <div class="card-title">target-druggability-assessment</div>
      <div class="card-desc">Evaluates macromolecular binding pocket volume, hydrophobicity, enclosure, and druggability scores.</div>
    </div>
    <div class="card">
      <div class="card-title">a11y-debugging & debug-optimize-lcp & memory-leak-debugging</div>
      <div class="card-desc">Chrome DevTools MCP workflows for Core Web Vitals (LCP), memory leak diagnosis (heapsnapshots), and accessibility audits.</div>
    </div>
    <div class="card">
      <div class="card-title">accidental-data-loss-prevention & skill-repair</div>
      <div class="card-desc">Enforces safety verification before destructive commands and auto-heals failed agent skills in manifests.</div>
    </div>
  </div>

  <!-- CHAPTER 9 -->
  <div class="chapter-header" id="ch9">
    <div class="chapter-num">Chapter 9</div>
    <div class="chapter-title">The 3 User Tiers: Unlocking 100% Potential</div>
  </div>

  <div class="card tier-rookie">
    <div class="card-top">
      <span class="card-title">🟢 Level 1: The Rookie (0% – 30% Potential)</span>
      <span class="badge green">Getting Started</span>
    </div>
    <div class="card-desc">
      • <strong>Stop Copy-Pasting:</strong> Never paste 500 lines of code into chat. Reference files with <code>@</code> so the agent reads tight line-bounded slices.<br>
      • <strong>Single-Key Tab:</strong> Adopt <kbd>Tab</kbd> for inline autocomplete, auto-imports, and cursor jumps.<br>
      • <strong>Start with <code>/plan</code>:</strong> Review the agent's interactive blueprint before any code is modified.
    </div>
  </div>

  <div class="card tier-pro">
    <div class="card-top">
      <span class="card-title">🟡 Level 2: The Pro (30% – 70% Potential)</span>
      <span class="badge amber">Closed-Loop Operator</span>
    </div>
    <div class="card-desc">
      • <strong>Closed-Loop Healing:</strong> Pair every implementation with an execution command: <em>"Refactor X in <code>src/engine.py</code> and run <code>pytest -v</code>. Diagnose failures and fix until all pass."</em><br>
      • <strong>Inline Transforms:</strong> Use <kbd>Ctrl</kbd>+<kbd>I</kbd> for localized refactoring without opening chat.<br>
      • <strong>Multi-Tool Chaining:</strong> Combine BioNeMo docking + RDKit sanitization + GitHub PR in a single prompt.<br>
      • <strong>Automated QA:</strong> Deploy <code>browser_subagent</code> to verify UI components and record video proof.
    </div>
  </div>

  <div class="card tier-master">
    <div class="card-top">
      <span class="card-title">🔴 Level 3: The Peak Master (70% – 100% Potential)</span>
      <span class="badge rose">Fleet Orchestrator</span>
    </div>
    <div class="card-desc">
      • <strong>Lead Orchestrator Architecture:</strong> Shield parent context. The parent acts exclusively as Lead Architect, consuming structured diffs and delegating tasks.<br>
      • <strong>Exact Model Matching:</strong> Sonnet 5.5 for UI styling, Opus 5.5 / Pro for deep architecture and race conditions, Flash 3.8 for high-speed execution.<br>
      • <strong>Autonomous Endurance (<code>/goal</code>):</strong> Run multi-hour benchmark sweeps or full-suite refactors without stopping.<br>
      • <strong>Persistent Memory Engineering:</strong> Codify project guidelines into <code>.agents/rules/</code> so every session starts at 100% calibration.<br>
      • <strong>Token Economics:</strong> Track exact token burns via <code>python scripts/token_tracker.py</code> and eliminate polling waste.
    </div>
  </div>

  <!-- CHAPTER 10 -->
  <div class="chapter-header" id="ch10">
    <div class="chapter-num">Chapter 10</div>
    <div class="chapter-title">Token Economics, Context Preservation & Audit Analytics</div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">Your Audited Token Consumption (All-Time)</span>
      <span class="badge blue">Audited Analytics</span>
    </div>
    <div class="card-desc">
      • <strong>Total Sessions Recorded:</strong> 13 sessions<br>
      • <strong>Total Conversation Turns:</strong> 10,695 steps<br>
      • <strong>Prompt / Input Tokens:</strong> 409,297 tokens (11.3%)<br>
      • <strong>Completion / Output Tokens:</strong> 3,222,986 tokens (88.7%)<br>
      • <strong>🔥 Grand Total Burned Tokens:</strong> <strong>3,632,283 tokens (~3.63M)</strong><br>
      • <strong>Average Tokens per Step:</strong> 339 tokens / step
    </div>
    <div class="card-meta">
      Run anytime in terminal: <code>python scripts/token_tracker.py</code>
    </div>
  </div>

  <div class="callout rose">
    <strong>The 5 Golden Rules of Zero-Token-Waste Engineering:</strong><br>
    1. <strong>Never Dump Raw Logs:</strong> Instruct the agent to run the command directly and grep the relevant failure line.<br>
    2. <strong>Surgical File Slicing:</strong> Use <code>view_file</code> with <code>StartLine</code>/<code>EndLine</code> instead of loading whole files (saves 85% input tokens).<br>
    3. <strong>Reactive Wakeup:</strong> Never poll with sleep loops; let the system wake the agent on task exit.<br>
    4. <strong>Atomic Multi-Site Updates:</strong> Use <code>multi_replace_file_content</code> to perform all edits in a single turn.<br>
    5. <strong>Session Freshness:</strong> Start new chat sessions for new major features; anchor permanent context into <code>.agents/rules/</code> instead of dragging 150-turn histories.
  </div>

  <footer>
    The Antigravity IDE Master Encyclopedia • Comprehensive Edition • Ready for Offline Mobile & PDF Reading
  </footer>

</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"HTML Encyclopedia created: {html_path} ({len(content)} chars)")

# Compile to PDF
edge_exe = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
chrome_exe = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
browser = chrome_exe if os.path.exists(chrome_exe) else edge_exe

cmd = [
    browser,
    '--headless=new',
    '--disable-gpu',
    '--no-pdf-header-footer',
    f'--print-to-pdf={pdf_path}',
    f'file:///{html_path}'
]

print("Compiling Master PDF via headless browser...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("PDF compiled:", os.path.exists(pdf_path), f"Size: {os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0} bytes")

# Sync to all target drives
destinations = [
    r'D:\ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.pdf',
    r'D:\BIONEMO\ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.pdf',
    r'D:\ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.html',
    r'D:\BIONEMO\ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.html',
    os.path.expanduser('~/OneDrive/Documents/ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.pdf'),
    os.path.expanduser('~/OneDrive/Documents/ANTIGRAVITY_IDE_ULTIMATE_ENCYCLOPEDIA.html'),
]

for d in destinations:
    try:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        src = pdf_path if d.endswith('.pdf') else html_path
        shutil.copy2(src, d)
        print(f"Synced to: {d}")
    except Exception as e:
        print(f"Failed to sync {d}: {e}")

print("Master Encyclopedia generation complete.")
