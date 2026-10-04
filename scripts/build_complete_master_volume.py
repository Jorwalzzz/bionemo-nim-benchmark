#!/usr/bin/env python3
"""
Antigravity IDE Complete Master Volume Compiler
Compiles an exhaustive, multi-chapter encyclopedia documenting:
- The 3 AI Modalities
- The 7 Models & Reasoning Tiers
- All Interactive UI & Slash Commands
- All 17 Core Native Tools
- All 33 MCP Servers and their 200+ Tools
- All 57 Specialized Skills with parameters, triggers, and examples
- The 3 User Mastery Levels (0% to 100% Potential)
- Token Economics, Context Preservation & Audit Analytics
Outputs:
1. ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.html
2. ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.pdf
3. ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.md
Syncs to Drive D and OneDrive for instant mobile reading.
"""

import os
import glob
import json
import subprocess
import shutil

html_out = os.path.abspath("ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.html")
pdf_out = os.path.abspath("ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.pdf")
md_out = os.path.abspath("ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.md")

# 1. Collect all MCP servers and their JSON schemas
mcp_base = os.path.expanduser("~/.gemini/antigravity-ide/mcp")
mcp_dirs = sorted(glob.glob(os.path.join(mcp_base, "*")))
mcp_data = {}

for m_dir in mcp_dirs:
    server_name = os.path.basename(m_dir)
    json_tools = sorted(glob.glob(os.path.join(m_dir, "*.json")))
    tools_list = []
    for jt in json_tools:
        tool_name = os.path.splitext(os.path.basename(jt))[0]
        desc = ""
        params = []
        try:
            with open(jt, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                desc = data.get("description", "No description provided.")
                props = data.get("parameters", {}).get("properties", {})
                params = list(props.keys())
        except Exception:
            pass
        tools_list.append({"name": tool_name, "description": desc, "parameters": params})
    if tools_list:
        mcp_data[server_name] = tools_list

# 2. Collect all Skills and their YAML frontmatter/descriptions
skills_paths = sorted(
    glob.glob(os.path.expanduser("~/.gemini/config/plugins/**/SKILL.md"), recursive=True) +
    glob.glob(os.path.expanduser("~/.gemini/config/skills/**/SKILL.md"), recursive=True) +
    glob.glob(os.path.expanduser("~/.gemini/antigravity-ide/builtin/skills/**/SKILL.md"), recursive=True) +
    glob.glob("c:/Users/jorwa/Documents/antigravity/BIONEMO/.agents/skills/**/SKILL.md", recursive=True)
)

skills_data = []
seen_skills = set()

for sp in skills_paths:
    skill_name = os.path.basename(os.path.dirname(sp))
    if skill_name in seen_skills:
        continue
    seen_skills.add(skill_name)
    desc = ""
    category = "General"
    if "science" in sp.lower():
        category = "Bioinformatics & Science"
    elif "bionemo" in sp.lower():
        category = "BioNeMo & NIM Inference"
    elif "chrome-devtools" in sp.lower():
        category = "Browser & QA"
    else:
        category = "Core IDE & Governance"

    try:
        with open(sp, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            in_yaml = False
            for line in lines[:30]:
                if line.strip() == "---":
                    in_yaml = not in_yaml
                    continue
                if in_yaml and line.startswith("description:"):
                    desc = line.split("description:", 1)[1].strip()
                    break
    except Exception:
        pass
    if not desc:
        desc = "Specialized agent workflow skill."
    skills_data.append({"name": skill_name, "category": category, "description": desc, "path": sp})

skills_data.sort(key=lambda x: (x["category"], x["name"]))

# 3. Assemble HTML Content
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>The Antigravity IDE Complete Master Volume: 100% Potential Decoded</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
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
    }}
    @page {{
      margin: 12mm;
      size: A4 portrait;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      line-height: 1.6;
      padding: 24px 16px 80px;
      -webkit-font-smoothing: antialiased;
      max-width: 900px;
      margin: 0 auto;
    }}
    header {{
      text-align: center;
      padding: 30px 10px 24px;
      border-bottom: 2px solid var(--border);
      margin-bottom: 30px;
    }}
    .badge-hero {{
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
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.25;
      margin-bottom: 8px;
    }}
    .subtitle {{
      font-size: 14px;
      color: var(--text-muted);
      max-width: 650px;
      margin: 0 auto;
    }}
    .chapter-header {{
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.12), transparent);
      border-left: 5px solid var(--primary);
      padding: 14px 18px;
      margin: 45px 0 20px;
      border-radius: 0 12px 12px 0;
      page-break-after: avoid;
    }}
    .chapter-num {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--primary);
      margin-bottom: 2px;
    }}
    .chapter-title {{
      font-size: 19px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #fff;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 14px;
      page-break-inside: avoid;
    }}
    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .card-title {{
      font-size: 15px;
      font-weight: 700;
      color: #fff;
    }}
    .badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .badge.blue {{ background: var(--primary-glow); color: var(--primary); border: 1px solid var(--border-accent); }}
    .badge.green {{ background: var(--green-glow); color: var(--green); border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge.purple {{ background: var(--purple-glow); color: var(--purple); border: 1px solid rgba(168, 85, 247, 0.3); }}
    .badge.amber {{ background: var(--amber-glow); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge.rose {{ background: var(--rose-glow); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }}

    .card-desc {{
      font-size: 13.5px;
      color: #cbd5e1;
      margin-bottom: 8px;
    }}
    .card-meta {{
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 8px;
      margin-top: 8px;
      font-size: 12.5px;
      color: var(--text-muted);
    }}
    .card-meta strong {{ color: #f1f5f9; }}
    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
      color: #38bdf8;
      background: rgba(15, 23, 42, 0.85);
      padding: 2px 6px;
      border-radius: 4px;
    }}
    kbd {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 4px;
      background: #1e293b;
      color: #f8fafc;
      border: 1px solid #334155;
    }}
    .callout {{
      background: rgba(56, 189, 248, 0.08);
      border-left: 4px solid var(--primary);
      border-radius: 0 10px 10px 0;
      padding: 14px 16px;
      margin: 16px 0;
      font-size: 13.5px;
    }}
    .callout.amber {{ background: var(--amber-glow); border-left-color: var(--amber); }}
    .callout.rose {{ background: var(--rose-glow); border-left-color: var(--rose); }}
    footer {{
      text-align: center;
      margin-top: 60px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--text-muted);
    }}
  </style>
</head>
<body>

  <header>
    <div class="badge-hero">Definitive 100% Operating Manual</div>
    <h1>The Antigravity IDE Master Volume</h1>
    <p class="subtitle">Complete Exhaustive Documentation: Every Surface, Model, Modality, Tool, All 33 MCP Servers ({sum(len(v) for v in mcp_data.values())} Tools), and All {len(skills_data)} Skills.</p>
  </header>

  <!-- CHAPTER 1: MODALITIES -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 1</div>
    <div class="chapter-title">The 3 Core AI Modalities in Antigravity IDE</div>
  </div>
  <div class="card">
    <div class="card-top">
      <span class="card-title">A. Passive Modality: Antigravity Tab Autocomplete & Supercomplete</span>
      <span class="badge green">Next-Intent Prediction</span>
    </div>
    <div class="card-desc">Continuous next-intent prediction engine running silently on every keystroke, synthesizing surrounding tabs, terminal outputs, recent diffs, and clipboard context.</div>
    <div class="card-meta">
      • <strong>Tab to Jump:</strong> Anticipates your next navigation point across lines; press <kbd>Tab</kbd> to jump forward.<br>
      • <strong>Tab to Import:</strong> Automatically resolves and inserts missing imports at the top of the file without disrupting cursor line position.<br>
      • <strong>Supercomplete:</strong> Displays floating multi-line refactorings and deletions right in your code canvas.<br>
      • <strong>Controls:</strong> <kbd>Tab</kbd> accepts full suggestion, <kbd>Esc</kbd> cancels, <kbd>Ctrl</kbd>+<kbd>→</kbd> accepts word-by-word.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">B. Instructive Modality: Inline Command (<kbd>Ctrl</kbd>+<kbd>I</kbd> / <kbd>Cmd</kbd>+<kbd>I</kbd>)</span>
      <span class="badge blue">In-Editor Surgical Edits</span>
    </div>
    <div class="card-desc">Surgical in-place code modification without switching mental context to the chat sidebar.</div>
    <div class="card-meta">
      • <strong>Targeted Refactoring:</strong> Highlight a specific code block, hit <kbd>Ctrl</kbd>+<kbd>I</kbd>, and prompt: <em>"Convert to async/await"</em> or <em>"Vectorize with NumPy"</em>. Only the highlighted lines are touched.<br>
      • <strong>Net-New Generation:</strong> Trigger <kbd>Ctrl</kbd>+<kbd>I</kbd> on an empty line with a descriptive prompt to generate boilerplate, classes, or test cases directly at the cursor.<br>
      • <strong>Instant Documentation:</strong> Highlight any function and trigger <kbd>Ctrl</kbd>+<kbd>I</kbd> with <em>"Add type annotations and Sphinx docstrings"</em>.
    </div>
  </div>

  <div class="card">
    <div class="card-top">
      <span class="card-title">C. Collaborative Modality: Sidebar Chat & Agent Mode</span>
      <span class="badge purple">Full-Stack Pair Programmer</span>
    </div>
    <div class="card-desc">The full agentic pair programmer capable of multi-step autonomous reasoning, executing shell commands, reading file trees, diagnosing failures, and managing MCP tools.</div>
    <div class="card-meta">
      • <strong>Inline Code Lenses:</strong> Action triggers rendered directly above classes and functions (<em>"Explain"</em>, <em>"Write Unit Tests"</em>, <em>"Refactor"</em>).<br>
      • <strong>Diagnostic Auto-Fix:</strong> Click on compiler errors, lint squiggly lines, or Problems pane entries to invoke the agent directly to analyze and heal the issue.<br>
      • <strong>Visual Diff Overlays:</strong> Review inline red/green diffs directly inside your editor canvas before committing changes.
    </div>
  </div>

  <!-- CHAPTER 2: MODELS -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 2</div>
    <div class="chapter-title">The 7 Exact Models & Reasoning Tiers</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">Gemini 3.8 Flash (Medium / Low)</span><span class="badge green">⚡ Ultra Fast Daily Driver</span></div>
    <div class="card-desc"><strong>The Daily Workhorse (80% of all programming tasks).</strong> Sub-second latency, highest MCP tool execution speed, lowest token burn, and massive context capacity.</div>
    <div class="card-meta"><strong>Best For:</strong> Writing functions, running pytest, CLI benchmarks, high-volume file edits.<br><strong>Avoid For:</strong> Abstract mathematical architecture with 15+ circular dependencies.</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">Claude Sonnet 5.5 (Medium)</span><span class="badge amber">🎨 Gold Standard UI & Clean Code</span></div>
    <div class="card-desc"><strong>Unmatched frontend design aesthetics and idiomatic code taste.</strong> Produces stunning, modern web apps (CSS/JS) and pristine, typed Python refactors.</div>
    <div class="card-meta"><strong>Best For:</strong> BioNeMo Cockpit UI, modern CSS/JS interfaces, clean architecture.<br><strong>Avoid For:</strong> Trivial shell loops or repetitive regex transforms.</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">Claude Opus 5.5 (Medium)</span><span class="badge rose">🧠 Maximum Cognitive Depth (S-Tier)</span></div>
    <div class="card-desc"><strong>Supreme architectural and mathematical reasoning.</strong> Solves novel algorithmic challenges, high-stakes system redesigns, and hard bug autopsies.</div>
    <div class="card-meta"><strong>Best For:</strong> Designing core algorithms from scratch, multi-module pipeline graphs.<br><strong>Avoid For:</strong> Fast back-and-forth chat or budget-limited sessions.</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">Gemini 3.1 Pro (Low)</span><span class="badge purple">🧠 Deliberate Logic & Concurrency</span></div>
    <div class="card-desc"><strong>Deliberate multi-hop reasoning.</strong> Traces complex concurrency bugs, race conditions, memory leaks, and interface contracts.</div>
    <div class="card-meta"><strong>Best For:</strong> Diagnosing subtle pipeline crashes, security audits, schema boundaries.<br><strong>Avoid For:</strong> Simple one-line edits or trivial renames.</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">Gemini 3.7 Flash & 3.6 Flash</span><span class="badge blue">⚡ Proven Stability & Batch</span></div>
    <div class="card-desc">Proven, stable instruction following. Consistent JSON schema adherence without bleeding-edge drift; great for repetitive batch scripts.</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">GPT-OSS 120B (Medium)</span><span class="badge amber">⚖️ Open-Weight Second Opinion</span></div>
    <div class="card-desc">Unbiased open-weights inference. Perfect for independent architectural reviews and cross-model code validation.</div>
  </div>

  <!-- CHAPTER 3: UI & SLASHES -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 3</div>
    <div class="chapter-title">Chat Canvas, @ Mentions & Slash Commands</div>
  </div>
  <div class="card">
    <div class="card-meta">
      • <code>@Files & Folders</code>: Attaches file paths so the agent reads surgical slices.<br>
      • <code>@Previous Conversations</code>: Bridges context from past debugging sessions.<br>
      • <code>@Terminal Sessions</code>: Injects terminal output without manual copying.<br>
      • <code>@Rules</code>: Enforces specific coding guidelines on demand.<br>
      • <code>@MCP Tools</code>: Explicitly targets a specific MCP tool suite.<br>
      • <code>/plan</code>: Interactive, phased blueprint before touching any code.<br>
      • <code>/goal</code>: Autonomous endurance mode; runs continuous execution loops until finished.<br>
      • <code>/grill-me</code>: Interviews you like a Staff Engineer to tease out edge cases.<br>
      • <code>/learn</code>: Saves corrected rules and workflows into permanent memory across sessions.<br>
      • <code>/schedule</code>: Configures one-shot timers or recurring cron triggers.
    </div>
  </div>

  <!-- CHAPTER 4: NATIVE TOOLS -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 4</div>
    <div class="chapter-title">The 17 Core Native Tools</div>
  </div>
  <div class="card">
    <div class="card-meta">
      • <code>view_file</code>: Reads text, images, PDFs, videos with precise line slices (<code>StartLine</code>/<code>EndLine</code>).<br>
      • <code>replace_file_content</code>: Surgically replaces a single contiguous block of code.<br>
      • <code>multi_replace_file_content</code>: Performs multiple non-contiguous edits atomically.<br>
      • <code>write_to_file</code>: Creates new files or overwrites existing files.<br>
      • <code>grep_search</code>: High-speed ripgrep search matching exact strings or regex across files.<br>
      • <code>list_dir</code>: Recursively lists directory contents and file sizes.<br>
      • <code>run_command</code>: Executes PowerShell commands in the user's workspace.<br>
      • <code>manage_task</code>: Controls background processes (<code>list</code>, <code>kill</code>, <code>status</code>, <code>send_input</code>).<br>
      • <code>schedule</code>: Configures asynchronous timers or cron jobs for reactive wakeup.<br>
      • <code>search_web</code>: Live search engine queries for real-time documentation.<br>
      • <code>read_url_content</code>: Fetches HTTP content converted directly to Markdown.<br>
      • <code>generate_image</code>: Generates UI mockups, diagrams, and visual assets.<br>
      • <code>browser_subagent</code>: Automated browser worker with WebP session recording.<br>
      • <code>ask_question</code>: Interactive multiple-choice prompt modal in the UI.<br>
      • <code>call_mcp_tool</code>: Invokes lazy-loaded MCP server endpoints.<br>
      • <code>read_resource</code>: Reads schemas or persistent state from an MCP server.<br>
      • <code>list_resources</code>: Lists all available resources exposed by an MCP server.
    </div>
  </div>

  <!-- CHAPTER 5: ALL MCP SERVERS -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 5</div>
    <div class="chapter-title">Complete MCP Server Ecosystem ({len(mcp_data)} Servers, {sum(len(v) for v in mcp_data.values())} Tools)</div>
  </div>
  <p>Here is every active Model Context Protocol (MCP) server registered in your environment, along with every tool it exposes and its exact function:</p>
"""

# Append every MCP server
for s_name, t_list in mcp_data.items():
    html_content += f"""
  <div class="card">
    <div class="card-top">
      <span class="card-title">🔌 Server: {s_name}</span>
      <span class="badge blue">{len(t_list)} Tools</span>
    </div>
    <div class="card-meta">
"""
    for t in t_list:
        p_str = f" <em>({', '.join(t['parameters'][:4])})</em>" if t['parameters'] else ""
        html_content += f"      • <code>{t['name']}</code>{p_str}: {t['description']}<br>\n"
    html_content += """    </div>
  </div>
"""

# CHAPTER 6: ALL 57 SKILLS
html_content += f"""
  <!-- CHAPTER 6: ALL 57 SKILLS -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 6</div>
    <div class="chapter-title">Complete 57-Skills Encyclopedia</div>
  </div>
  <p>Every specialized agent skill loaded across your science, BioNeMo, browser debugging, and governance roots:</p>
"""

current_cat = ""
for sk in skills_data:
    if sk["category"] != current_cat:
        current_cat = sk["category"]
        html_content += f"""
  <h3 style="color: var(--primary); margin: 24px 0 10px;">🏷️ {current_cat}</h3>
"""
    html_content += f"""
  <div class="card">
    <div class="card-top">
      <span class="card-title">📖 {sk['name']}</span>
      <span class="badge purple">{sk['category'].split()[0]}</span>
    </div>
    <div class="card-desc">{sk['description']}</div>
  </div>
"""

# CHAPTER 7: MASTERY TIERS & TOKEN ECONOMICS
html_content += f"""
  <!-- CHAPTER 7: MASTERY TIERS -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 7</div>
    <div class="chapter-title">The 3 User Tiers: Unlocking 100% Potential</div>
  </div>
  <div class="card" style="border-left: 4px solid var(--green);">
    <div class="card-top"><span class="card-title">🟢 Level 1: The Rookie (0% – 30% Potential)</span><span class="badge green">Rookie</span></div>
    <div class="card-desc">Stop copy-pasting code into chat. Reference files with <code>@</code> so the agent reads tight line-bounded slices. Adopt single-key <kbd>Tab</kbd> for inline autocomplete, auto-imports, and cursor jumps. Start features with <code>/plan</code>.</div>
  </div>
  <div class="card" style="border-left: 4px solid var(--amber);">
    <div class="card-top"><span class="card-title">🟡 Level 2: The Pro (30% – 70% Potential)</span><span class="badge amber">Pro</span></div>
    <div class="card-desc">Closed-loop autonomous healing: pair every implementation with a terminal test (<em>"Edit X, run pytest, diagnose tracebacks, and fix until all pass"</em>). Use <kbd>Ctrl</kbd>+<kbd>I</kbd> for localized in-editor refactoring. Chain multiple MCP toolsets in a single prompt. Deploy <code>browser_subagent</code> for visual QA.</div>
  </div>
  <div class="card" style="border-left: 4px solid var(--rose);">
    <div class="card-top"><span class="card-title">🔴 Level 3: The Peak Master (70% – 100% Potential)</span><span class="badge rose">100% Master</span></div>
    <div class="card-desc">Lead Orchestrator Architecture: shield parent context at all costs. Match model tiers exactly (Sonnet for UI, Opus/Pro for deep architecture, Flash for execution). Run autonomous multi-hour sweeps with <code>/goal</code>. Codify permanent rules in <code>.agents/rules/</code>. Monitor token consumption with <code>python scripts/token_tracker.py</code>.</div>
  </div>

  <!-- CHAPTER 8: TOKEN AUDIT -->
  <div class="chapter-header">
    <div class="chapter-num">Chapter 8</div>
    <div class="chapter-title">Token Economics & Audit Analytics</div>
  </div>
  <div class="card">
    <div class="card-top"><span class="card-title">Your Audited Historical Usage (13 Sessions)</span><span class="badge blue">Audited</span></div>
    <div class="card-desc">
      • Total Conversation Steps: <strong>10,695 turns</strong><br>
      • Prompt Tokens: <strong>409,297</strong> (11.3%) | Completion Tokens: <strong>3,222,986</strong> (88.7%)<br>
      • 🔥 Grand Total Burned Tokens: <strong>3,632,283 tokens (~3.63M)</strong><br>
      • Average Tokens per Step: <strong>339 tokens</strong><br>
      • Run anytime in terminal: <code>python scripts/token_tracker.py</code>
    </div>
  </div>

  <footer>
    The Antigravity IDE Master Volume • Comprehensive Encyclopedia • Offline Mobile & PDF Edition
  </footer>

</body>
</html>
"""

with open(html_out, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Master HTML Volume created: {html_out} ({len(html_content)} bytes)")

# Convert to Markdown version as well
md_lines = [
    "# The Antigravity IDE Complete Master Volume: 100% Potential Decoded\n",
    f"> **The Complete Exhaustive Reference: 3 Modalities, 7 Models, 17 Native Tools, {len(mcp_data)} MCP Servers ({sum(len(v) for v in mcp_data.values())} Tools), and {len(skills_data)} Specialized Skills.**\n\n---\n"
]

md_lines.append("## 1. The 3 Core AI Modalities\n")
md_lines.append("- **Passive: Antigravity Tab**: Real-time next-intent prediction, Tab to Jump, Tab to Import, Supercomplete floating diffs.\n")
md_lines.append("- **Instructive: Inline Command (`Ctrl+I` / `Cmd+I`)**: Surgical in-editor code refactoring, code generation at cursor, localized docstrings.\n")
md_lines.append("- **Collaborative: Sidebar Chat & Agent Mode**: Full-stack pair programming, inline code lenses, diagnostic auto-fix, visual diff overlays.\n\n---\n")

md_lines.append("## 2. The 7 Exact Models & Selection Matrix\n")
md_lines.append("1. **Gemini 3.8 Flash (Medium/Low)**: Daily workhorse (80% of tasks), ultra-fast latency, lowest token burn.\n")
md_lines.append("2. **Claude Sonnet 5.5 (Medium)**: Gold standard for UI design (CSS/JS) and pristine typed Python refactors.\n")
md_lines.append("3. **Claude Opus 5.5 (Medium)**: Maximum cognitive depth (S-tier), novel algorithms, multi-module architecture.\n")
md_lines.append("4. **Gemini 3.1 Pro (Low)**: Deliberate multi-hop reasoning, subtle race conditions, memory leaks, security audits.\n")
md_lines.append("5. **Gemini 3.7 Flash & 3.6 Flash**: Stable JSON schema output and high-volume batch processing.\n")
md_lines.append("6. **GPT-OSS 120B (Medium)**: Neutral open-weights second opinions and independent code review.\n\n---\n")

md_lines.append(f"## 3. Complete MCP Server Ecosystem ({len(mcp_data)} Servers, {sum(len(v) for v in mcp_data.values())} Tools)\n")
for s_name, t_list in mcp_data.items():
    md_lines.append(f"### 🔌 `{s_name}` ({len(t_list)} Tools)\n")
    for t in t_list:
        p_str = f" *({', '.join(t['parameters'][:4])})*" if t['parameters'] else ""
        md_lines.append(f"- **`{t['name']}`**{p_str}: {t['description']}\n")
    md_lines.append("\n")

md_lines.append(f"\n---\n## 4. Complete {len(skills_data)}-Skills Encyclopedia\n")
curr_c = ""
for sk in skills_data:
    if sk["category"] != curr_c:
        curr_c = sk["category"]
        md_lines.append(f"\n### 🏷️ {curr_c}\n")
    md_lines.append(f"- **`{sk['name']}`**: {sk['description']}\n")

with open(md_out, "w", encoding="utf-8") as f:
    f.writelines(md_lines)
print(f"Master Markdown Volume created: {md_out} ({len(md_lines)} lines)")

# Compile to PDF
edge_exe = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
chrome_exe = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
browser = chrome_exe if os.path.exists(chrome_exe) else edge_exe

cmd = [
    browser,
    '--headless=new',
    '--disable-gpu',
    '--no-pdf-header-footer',
    f'--print-to-pdf={pdf_out}',
    f'file:///{html_out}'
]

print("Compiling Master PDF Volume...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("PDF compiled:", os.path.exists(pdf_out), f"Size: {os.path.getsize(pdf_out) if os.path.exists(pdf_out) else 0} bytes")

# Sync to all target drives
destinations = [
    r'D:\ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.pdf',
    r'D:\BIONEMO\ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.pdf',
    r'D:\ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.html',
    r'D:\BIONEMO\ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.html',
    r'D:\BIONEMO\ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.md',
    os.path.expanduser('~/OneDrive/Documents/ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.pdf'),
    os.path.expanduser('~/OneDrive/Documents/ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.html'),
    os.path.expanduser('~/OneDrive/Documents/ANTIGRAVITY_IDE_COMPLETE_MASTER_VOLUME.md'),
]

for d in destinations:
    try:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if d.endswith('.pdf'):
            shutil.copy2(pdf_out, d)
        elif d.endswith('.html'):
            shutil.copy2(html_out, d)
        elif d.endswith('.md'):
            shutil.copy2(md_out, d)
        print(f"Synced to: {d}")
    except Exception as e:
        print(f"Failed to sync {d}: {e}")

print("Master Volume generation and cloud sync complete!")
