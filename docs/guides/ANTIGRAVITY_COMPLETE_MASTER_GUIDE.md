# The Complete Antigravity IDE Master Guide: 100% Potential Decoded

> **The Definitive Operating Manual for Antigravity IDE: Modalities, Models, Chat Canvas, Settings, Subagents, MCP Suites, and Mastery Tiers (Rookie to Peak Master).**

---

## 📑 Quick Navigation
1. [The 3 Core AI Modalities](#1-the-3-core-ai-modalities-in-antigravity-ide)
2. [The 7 Exact Models & Reasoning Tiers](#2-the-7-exact-models--reasoning-tiers)
3. [Chat Canvas, @ Mentions & Slash Commands](#3-chat-canvas--mentions--slash-commands)
4. [Settings, Policies & Security Sandboxes](#4-settings-policies--security-sandboxes)
5. [Subagents & Background Execution](#5-subagents--background-execution)
6. [Core Tools & Integrated MCP Suites](#6-core-tools--integrated-mcp-suites)
7. [The 3 User Tiers: Unlocking 100% Potential](#7-the-3-user-tiers-unlocking-100-potential)
8. [Context Economics & Token Auditing](#8-context-economics--token-auditing)

---

## 1. The 3 Core AI Modalities in Antigravity IDE

Antigravity IDE gives you three distinct ways to interact with AI:

### A. Passive: Antigravity Tab (Autocomplete & Supercomplete)
* **Single Keystroke Prediction**: Runs in real time as you type code.
* **Tab to Jump**: Anticipates your next cursor position or function call; press `Tab` to jump forward.
* **Tab to Import**: Automatically resolves missing imports at the top of the file.
* **Supercomplete**: Floats larger diffs, including deletions and refactoring proposals.
* **Controls**: `Tab` to accept, `Esc` to dismiss, `Ctrl`+`Right` (or `Cmd`+`Right`) to accept word-by-word.

### B. Instructive: Inline Command (`Ctrl`+`I` / `Cmd`+`I`)
* **Surgical In-Place Edits**: Highlight a block of code, press `Ctrl`+`I`, and prompt (e.g., *"Vectorize this loop with NumPy"*). Only the highlighted block is changed.
* **Net-New Generation**: Trigger on a blank line to generate net-new functions or boilerplate at your cursor.
* **Localized Docs**: Quickly generate clean docstrings for highlighted functions.

### C. Collaborative: Sidebar Chat & Agent Mode
* **Full-Stack Pair Programmer**: Capable of reading and modifying files across the repository, running shell tests (`pytest`), managing background processes, and calling external MCP servers.
* **Inline Code Lenses**: Action buttons appearing above classes and functions (*"Explain"*, *"Write Tests"*, *"Refactor"*).
* **Diagnostic Auto-Fix**: Click compiler/linter squiggly lines or Problems pane entries to automatically apply agent fixes.
* **Visual Diff Overlays**: Review red/green line diffs directly inside the editor before confirming.

---

## 2. The 7 Exact Models & Reasoning Tiers

| Model Name & Badge | Tier | Speed | Reasoning Depth | Primary Superpower & Best Use | Avoid For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 3.8 Flash** *(Fast)* | Gemini Flash Gen 3.8 | ⚡ Ultra-Fast | Adaptive | **Daily Workhorse (80% of tasks)**: High-speed code editing, pytest runs, CLI benchmarks, lowest token burn. | Abstract mathematical proofs with 15+ circular dependencies. |
| **Claude Sonnet 5.5** *(New)* | Anthropic Balanced | ⚡ Fast-Medium | 🧠 High Precision | **Gold Standard for UI & Clean Code**: Gorgeous modern web styling (CSS/JS), pristine typed Python refactors. | Bare-bones repetitive searches or simple shell test assertions. |
| **Claude Opus 5.5** *(New)* | Anthropic Frontier | ⏱️ Deep Thinker | 🧠🧠 S-Tier Logic | **Maximum Cognitive Depth**: Writing novel algorithms from scratch, high-stakes system redesigns, difficult bug autopsies. | Fast back-and-forth chat or budget-limited sessions. |
| **Gemini 3.1 Pro** | Gemini Pro Gen 3.1 | ⏱️ Steady | 🧠 Deliberate Logic | **Deliberate Multi-Hop Logic**: Diagnosing race conditions, memory leaks, security audits, and complex pipeline graphs. | Simple one-line edits or trivial renames (waste of reasoning tokens). |
| **Gemini 3.7 Flash** *(Fast)* | Gemini Flash Gen 3.7 | ⚡ Very Fast | Solid Balanced | **Rock-Solid Stability**: Proven JSON schema adherence and tool calls without experimental drift. | Brand-new experimental syntax where 3.8 is sharper. |
| **Gemini 3.6 Flash** *(Fast)* | Gemini Flash Gen 3.6 | ⚡ Very Fast | Standard Fast | **Bulk Batch Work**: High-volume regex transforms, batch linting, repetitive maintenance. | Complex multi-turn debugging. |
| **GPT-OSS 120B** *(Notice)* | Open-Weight | ⏱️ Moderate | Solid Open Logic | **Unbiased Second Opinion**: Independent architectural review and cross-model code verification. | Highly complex multi-tool chaining (proprietary APIs have tighter hooks). |

### Reasoning Modifiers Explained:
* **`Low` Reasoning**: Bypasses internal thinking scratchpad; returns code immediately. Saves maximum tokens and execution time.
* **`Medium` Reasoning**: Runs an internal chain-of-thought analysis before outputting code. Prevents logic regressions in complex refactors.

---

## 3. Chat Canvas, @ Mentions & Slash Commands

### `@` Mentions (Surgical Context Injection)
* `@Files & Folders`: Injects exact paths so the agent reads line-bounded slices (`StartLine`/`EndLine`).
* `@Previous Conversations`: Pulls context from past debugging sessions without starting from scratch.
* `@Terminal Sessions`: Attaches terminal output directly into prompt context.
* `@Rules`: Enforces project-specific guidelines on demand.
* `@MCP Tools`: Targets a specific Model Context Protocol tool suite.

### Slash Commands
* **`/plan`**: Formulates an interactive, phased blueprint before touching any code.
* **`/goal`**: Autonomous endurance mode; runs continuous execution loops until finished.
* **`/grill-me`**: Interviews you like a Staff Engineer to tease out edge cases and assumptions.
* **`/learn`**: Saves corrected rules and workflows into permanent memory across sessions.
* **`/schedule`**: Configures one-shot timers or recurring cron triggers.

---

## 4. Settings, Policies & Security Sandboxes

* **Tool Execution Policy**: Choose `always-proceed` for maximum autonomy, `request-review` for step-by-step confirmation, or `proceed-in-sandbox`.
* **Terminal Sandbox**: Runs shell commands inside an isolated environment to protect host files.
* **Non-Workspace File Access**: Restricts agent file operations to the current workspace root (`allow`, `ask`, `deny`).
* **Accidental Data Loss Prevention**: Built-in safety guards preventing destructive commands (`DROP TABLE`, broad file wipes) without explicit confirmation.

---

## 5. Subagents & Background Execution

* **Reactive Wakeup**: The agent never runs busy-waiting loops. It sleeps while long jobs run and resumes automatically when finished.
* **`browser_subagent`**: Automated browser that navigates local webapps, clicks elements, fills forms, tests viewports, audits accessibility, and records WebP session videos.
* **`manage_task`**: Inspects and controls background servers and benchmarks (`list`, `kill`, `status`, `send_input`).

---

## 6. Core Tools & Integrated MCP Suites

* **File Operations**: `view_file` (line slicing), `replace_file_content`, `multi_replace_file_content`, `write_to_file`.
* **Codebase Search**: `grep_search` (ripgrep string/regex), `list_dir`.
* **Terminal**: `run_command` (runs PowerShell in workspace).
* **BioNeMo NIM (`bionemo-tools`)**: `bionemo_query_diffdock`, `bionemo_query_esmfold`, `bionemo_query_esm2_embedding`, `bionemo_sanitize_smiles`, `bionemo_validate_sequence`, `bionemo_fetch_rcsb_pdb`, `bionemo_run_benchmark`.
* **GitHub MCP (`github-mcp-server`)**: Repo management, branches, commits, PR creation, reviews.
* **Stitch MCP (`StitchMCP`)**: Screen generation from text, UI design systems, visual variants.
* **Chrome DevTools (`chrome-devtools-mcp`)**: Lighthouse audits, network inspection, console errors, DOM evaluation.
* **Perplexity (`perplexity-ask`)**: Academic and web research with real citations.

---

## 7. The 3 User Tiers: Unlocking 100% Potential

### 🟢 Level 1: The Rookie (0% – 30% Potential)
* **Mistake**: Pasting 500 lines of code or error logs directly into chat.
* **Action**:
  1. Mention files with `@` (e.g., `@src/resistance_engine.py`) so the agent reads line-bounded slices.
  2. Use single-keystroke `Tab` for autocompletion, import resolution, and cursor jumps.
  3. Run `/plan` before starting multi-step tasks.

### 🟡 Level 2: The Pro (30% – 70% Potential)
* **Mistake**: Manually running tests and copying errors back and forth.
* **Action**:
  1. **Closed-Loop Healing**: Pair every code prompt with a verification command: *"Refactor X in `src/engine.py` and run `pytest -v`. Diagnose tracebacks and fix until all pass."*
  2. **Inline Transforms**: Use `Ctrl`+`I` for localized refactoring without opening chat.
  3. **Multi-Tool Chaining**: Chain BioNeMo docking + RDKit sanitization + GitHub PR in a single prompt.
  4. **Automated QA**: Deploy `browser_subagent` to verify UI components and record video proof.

### 🔴 Level 3: The Peak Master (70% – 100% Potential)
* **Mistake**: Letting the parent agent perform heavy file reads and command execution directly.
* **Action**:
  1. **Lead Orchestrator Architecture**: Shield parent context. The parent acts exclusively as Lead Architect, consuming structured diffs and delegating tasks.
  2. **Exact Model Matching**: Match the exact model to the problem (Sonnet 5.5 for UI styling, Opus 5.5 / Pro for deep architecture and race conditions, Flash 3.8 for high-speed execution).
  3. **Autonomous Endurance (`/goal`)**: Run multi-hour benchmark sweeps or full-suite refactors without stopping.
  4. **Persistent Memory Engineering**: Codify project guidelines into `.agents/rules/` so every session starts at 100% calibration.
  5. **Token Economics**: Monitor token burns via `python scripts/token_tracker.py` and eliminate polling waste.

---

## 8. Context Economics & Token Auditing

* **Local Audit Tool**: Run `python scripts/token_tracker.py` anytime to inspect historical consumption.
* **All-Time Workspace Stats**:
  * Total Sessions: `13 sessions`
  * Total Steps: `10,695 turns`
  * Grand Total Burned Tokens: **`3.63M tokens`**
  * Input vs. Output Ratio: **11.3% Input / 88.7% Output** (High prompt leverage).
* **Context Preservation Rule**: Slicing file reads (`StartLine`/`EndLine`) saves up to 85% of input tokens on every turn.
