# The Complete Antigravity Model & Mastery Reference Guide

> **An exhaustive, exact breakdown of all 7 models in your Antigravity dropdown menu, their reasoning tiers, cost/token efficiency profiles, strengths, weaknesses, and real-world selection matrix.**

---

## 🎯 The 7 Exact Models in Your Dropdown

Based on your Antigravity UI model selector:
1. **Gemini 3.8 Flash** (`Medium` / `Low` reasoning)
2. **Gemini 3.7 Flash** (`Medium` reasoning)
3. **Gemini 3.6 Flash** (`Medium` reasoning)
4. **Gemini 3.1 Pro** (`Low` reasoning)
5. **Claude Opus 5.5** (`Medium` reasoning)
6. **Claude Sonnet 5.5** (`Medium` reasoning)
7. **GPT-OSS 120B** (`Medium` reasoning)

---

## 📊 Comprehensive Model Comparison Matrix

| Model Name | Tier / Family | Speed & Latency | Reasoning Depth | Primary Superpower | Token & Cost Efficiency | When to Pick This Model | When to AVOID This Model |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 3.8 Flash** *(Fast)* | Gemini Flash Gen 3.8 | ⚡ Ultra Fast (Lowest latency) | Moderate-High (Adaptive thinking) | **Top-tier daily coding workhorse**; fastest tool execution & massive context throughput. | 🟢 Highest (Minimal token burn, maximum output/sec) | • Daily full-stack feature development<br>• Terminal execution & quick test fixes (`pytest`)<br>• High-volume MCP tool calls<br>• Rapid iterative prototyping | • Abstract multi-file architectural proofs with 15+ circular dependencies<br>• Ultra-deep philosophical or theoretical math |
| **Gemini 3.7 Flash** *(Fast)* | Gemini Flash Gen 3.7 | ⚡ Very Fast | Solid Balanced | Proven, highly stable instruction-following and structured JSON schema output. | 🟢 Very High | • Reliable benchmark profiling & script execution<br>• Structured API payloads (BioNeMo NIM endpoints)<br>• When you want rock-solid consistency without bleeding-edge drift | • Brand new experimental API patterns where 3.8 offers sharper code synthesis |
| **Gemini 3.6 Flash** *(Fast)* | Gemini Flash Gen 3.6 | ⚡ Very Fast | Standard Fast | Legacy stable Flash version; highly predictable behavior for simple workflows. | 🟢 High | • Repetitive maintenance tasks<br>• Simple lint fixes and regex transforms<br>• High-volume batch script processing | • Complex architectural reasoning or difficult multi-turn debugging |
| **Gemini 3.1 Pro** | Gemini Pro Gen 3.1 | ⏱️ Deliberate / Steady | 🧠 High Deliberate Logic | Deep multi-hop analysis, broad context synthesis, and rigorous edge-case tracing. | 🟡 Medium (More tokens burned on reasoning tokens) | • Designing complex system architectures and interfaces<br>• Tracing subtle race conditions & memory leaks<br>• Auditing security and API boundaries<br>• Complex biological pipeline graph planning | • Simple one-line edits or file renames (waste of reasoning overhead)<br>• Trivial grep lookups or boilerplate formatting |
| **Claude Opus 5.5** *(New)* | Anthropic Frontier | ⏱️ Slow / Deep Thinker | 🧠🧠 Maximum Cognitive Depth (S-Tier) | **Supreme architectural reasoning**, nuanced prose, elegant mathematical & algorithmic logic. | 🔴 Low (Highest token consumption, deep thinking) | • Designing core algorithms from scratch (e.g., custom scoring functions)<br>• High-stakes production refactoring<br>• Complex mathematical derivations or novel ML architectures<br>• Critical bug autopsies that other models fail to diagnose | • Fast back-and-forth iteration<br>• Running rapid shell loops or simple test assertions<br>• Budget-constrained high-turn sessions |
| **Claude Sonnet 5.5** *(New)* | Anthropic Balanced Frontier | ⚡ Fast-Medium | 🧠 High Precision Coding | **Gold standard for clean, idiomatic code generation**, pristine refactors, and aesthetic web frontends. | 🟡 Medium-High | • Writing beautiful, bug-free frontend code (CSS, JS, UI components)<br>• Refactoring messy legacy codebases into clean design patterns<br>• High-precision cheminformatics and typed Python modules<br>• Writing exhaustive docstrings and technical documentation | • Bare-bones quick file searches or repetitive batch script loops |
| **GPT-OSS 120B** *(Notice)* | Open-Weight Frontier | ⏱️ Moderate | Solid Open Logic | Unbiased open-weights inference, independent code synthesis, free from proprietary API quirks. | 🟡 Medium | • Neutral second opinions on architecture and code review<br>• Open-source alignment and cross-model code verification<br>• Fallback when proprietary endpoints experience upstream rate limits | • Highly specialized MCP tool chaining (proprietary models often have tighter tool calling hooks) |

---

## 🎚️ Understanding the Reasoning Modifiers: `Medium` vs `Low`

Notice the labels like `Medium` and `Low` next to model names (e.g., `Gemini 3.8 Flash Medium` vs `Gemini 3.8 Flash Low`):
* **`Low` Reasoning / Thinking**:
  * **Behavior**: Minimizes or bypasses the internal "thinking" scratchpad. The model responds immediately with direct code.
  * **Best For**: Fast edits, quick script runs, terminal commands, simple bug fixes, and saving token costs.
* **`Medium` Reasoning / Thinking**:
  * **Behavior**: Generates an internal chain-of-thought scratchpad before outputting code.
  * **Best For**: Multi-step debugging, planning complex diffs, preventing logic regressions, and verifying edge cases before writing.

---

## 🎯 Concrete Decision Playbook: What Model Should You Pick Right Now?

| If Your Immediate Task Is... | Select This Model | Why |
| :--- | :--- | :--- |
| **"I want to build, test, and debug BioNeMo benchmark scripts & run pytest"** | **Gemini 3.8 Flash (Medium or Low)** | Fastest speed, native tool calling, lowest token burn, great coding logic. |
| **"I want to build a stunning, premium UI cockpit for BioNeMo"** | **Claude Sonnet 5.5 (Medium)** | Unmatched design aesthetics, clean CSS/JS architecture, impeccable code taste. |
| **"I have an insidious, impossible concurrency/memory bug that keeps failing"** | **Claude Opus 5.5 (Medium)** or **Gemini 3.1 Pro (Low)** | Deepest cognitive trace analysis to locate race conditions and subtle logical flaws. |
| **"I want to design a massive multi-module biological pipeline architecture"** | **Claude Opus 5.5 (Medium)** | Best high-level structural planning and trade-off evaluation. |
| **"I want a completely independent code review of our pipeline"** | **GPT-OSS 120B (Medium)** | Open-weights architecture provides an unbiased second opinion. |
| **"I'm running a long automated batch script or 100+ tests"** | **Gemini 3.8 Flash (Low)** | Instant output without spending excess reasoning tokens on simple assertions. |

---

## 🚀 The 4-Tier User Journey (Rookie to 100% Potential)

### 🟢 Level 1: The Rookie (0% – 25% Potential)
* **Trap**: Pasting entire 2,000-line files or whole error logs into chat.
* **Action**: Reference exact file paths (e.g., `src/resistance_engine.py`). Use **`/plan`** before starting and **`/learn`** to lock in good patterns.

### 🟡 Level 2: The Intermediate (25% – 50% Potential)
* **Trap**: Manually testing code in terminal, copying errors back and forth.
* **Action**: Autonomous closed loops: *"Edit `src/baseline.py`, run `pytest -v`, diagnose tracebacks, and fix until all pass."* Run **`/grill-me`** before features to expose missing specs.

### 🟠 Level 3: The Pro (50% – 80% Potential)
* **Trap**: Treating the agent like an isolated Python writer.
* **Action**: Multi-MCP chaining (BioNeMo NIM ➔ RDKit ➔ GitHub PR) and **`browser_subagent`** automated web testing with WebP video recording. Enforce project rules in `.agents/rules/`.

### 🔴 Level 4: The 100% Potential Omniscient User (80% – 100% Potential)
* **Trap**: Running single-agent bloated contexts.
* **Action**:
  1. **Model Matching**: Match the exact model to the problem (Sonnet for UI, Opus/Pro for Architecture, Flash for Execution).
  2. **Parent Context Shielding**: Keep the lead orchestrator clean. Consume only summaries and line diffs.
  3. **Endurance Automation with `/goal`**: Continuous multi-hour autonomous execution with exponential backoff until complete.
