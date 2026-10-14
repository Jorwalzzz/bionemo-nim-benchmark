# Antigravity Complete Command & Tool Reference Guide

This comprehensive reference documents **every tool, slash command, MCP server tool, subagent, and specialized scientific capability** configured in your environment.

---

## 1. User Interactive Slash Commands (Chat UI)

| Slash Command | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`/plan`** | Prompts the agent to formulate an interactive, structured multi-phase execution plan before touching code. | Complex architectural refactoring, new module creation, or multi-step integrations. | Preventing circular work and agreeing on dependencies upfront. |
| **`/goal`** | Activates long-running, persistent autonomous execution where the agent will not stop until the objective is accomplished. | Overnight benchmark runs, exhaustive test suite fixes, full-pipeline end-to-end tasks. | Unattended, comprehensive task execution. |
| **`/grill-me`** | Conducts a targeted interview questioning you on edge cases, trade-offs, and implicit constraints. | At requirements gathering phase before starting an ambiguous task. | Eliminating requirement ambiguity and surfacing hidden edge cases. |
| **`/learn`** | Extracts and persists rules, customized user workflows, or corrected behaviors into permanent agent memory. | After correcting an agent mistake or establishing a project-specific pattern. | Cross-session personalization and avoiding repeated mistakes. |
| **`/schedule`** | Schedules a one-shot notification timer or a recurring background cron job. | Polling long asynchronous operations, recurring health checks, scheduled reminders. | Periodic monitoring and reactive wakeups without busy-waiting. |

---

## 2. Core Antigravity Agent Tools

| Tool Name | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`view_file`** | Reads slices or full contents of text, images, PDFs, videos, and audio. | Inspecting specific code sections with line ranges (`StartLine`/`EndLine`). | Token-efficient file inspection without context bloating. |
| **`replace_file_content`** | Surgically replaces a single contiguous block of text in an existing file. | Single-function updates, bug fixes, or localized config adjustments. | Precise, safe edits preserving untouched code. |
| **`multi_replace_file_content`**| Replaces multiple non-contiguous blocks of text across a file atomically. | Renaming variables across multiple functions, updating multiple imports simultaneously. | Multi-site refactoring without race conditions or partial writes. |
| **`write_to_file`** | Generates brand-new files or completely overwrites existing files. | Creating new modules, test files, markdown artifacts, or scripts. | Bootstrapping new codebase components. |
| **`grep_search`** | High-speed ripgrep search matching exact strings or regex patterns across files. | Locating symbol definitions, call sites, imports, or configuration keys. | Fast codebase reconnaissance without manual file walking. |
| **`list_dir`** | Recursively or shallowly lists directories, sizes, and file structures. | Exploring repository layouts or locating target directories. | Discovering file structures and project layouts. |
| **`run_command`** | Executes PowerShell/shell commands directly in the user workspace. | Running pytest, installing packages in `.venv`, executing CLI benchmarks. | Automation, testing, and local system actions. |
| **`manage_task`** | Interacts with background tasks (`list`, `kill`, `status`, `send_input`). | Managing long-running benchmarks, servers, or async build commands. | Controlling non-blocking background processes. |
| **`schedule`** | Schedules asynchronous timers (`DurationSeconds`) or cron jobs (`CronExpression`). | Setting periodic status checks or timeouts. | Preventing busy-wait loops and reducing token consumption. |
| **`ask_question`** | Renders an interactive multiple-choice prompt in the UI. | When requirements are ambiguous or critical architectural decisions need input. | Structured user clarification. |
| **`search_web`** | Performs web search via search engine for up-to-date documentation or papers. | Looking up recent library updates, docs, or scientific literature. | Retrieving real-time external information. |
| **`read_url_content`** | Fetches static HTTP content from a URL converted directly to Markdown. | Reading documentation pages, GitHub READMEs, or online articles. | Fast, invisible text extraction from public web pages. |
| **`generate_image`** | Generates visual assets or UI mockups using generative image models. | Creating diagrams, UI concepts, or visual assets. | Producing visual designs without device frames. |
| **`call_mcp_tool`** | Calls tools provided by lazily-loaded Model Context Protocol (MCP) servers. | Accessing external services (BioNeMo, Stitch, GitHub, Perplexity, Chrome DevTools). | Extending agent capabilities beyond native built-ins. |
| **`read_resource`** | Retrieves resource contents from an MCP server via a URI. | Reading schemas or persistent data registered by MCP servers. | Reading MCP server state or templates. |
| **`list_resources`** | Lists all available resources exposed by a specified MCP server. | Discovering available MCP assets. | Exploring MCP capabilities. |
| **`browser_subagent`** | Spawns an isolated browser subagent that navigates, tests, and records sessions. | E2E web testing, auditing web UIs, verifying frontend apps. | Automated UI verification and visual testing. |

---

## 3. NVIDIA BioNeMo & NIM Inference Tools (`bionemo-tools`)

| Tool Name | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`bionemo_validate_sequence`** | Validates amino acid sequences against canonical 20 IUPAC residues. | Before sending raw protein strings to ESM-2 or ESMFold. | Preventing invalid sequence payloads and API errors. |
| **`bionemo_sanitize_smiles`** | Performs RDKit sanitization and valence checks on small molecules. | Pre-processing ligand SMILES before molecular docking or generation. | Ensuring stereochemistry and valence validity. |
| **`bionemo_query_esm2_embedding`** | Queries ESM-2 protein language model to extract residue or per-protein embeddings. | Feature extraction for downstream classifiers or mutation scoring. | Fast zero-shot protein representations. |
| **`bionemo_query_esmfold`** | Predicts 3D atomic coordinates (`.pdb`) from raw protein sequences. | When experimental PDB structures are unavailable. | De novo structure prediction and pLDDT confidence scoring. |
| **`bionemo_query_diffdock`** | Performs generative molecular docking of small-molecule ligands to target proteins. | Screening drug candidates against receptor pockets. | Blind docking and binding pose prediction. |
| **`bionemo_fetch_rcsb_pdb`** | Fetches and cleans experimental macromolecular structures from RCSB PDB. | Retrieving target receptors (e.g., 6LU7, 1HSG, 2SRC). | Fetching ground-truth crystal structures. |
| **`bionemo_compare_known_inhibitors`** | Compares candidate compounds against known reference drugs/inhibitors. | Calculating chemical similarity, Tanimoto coefficients, and Lipinski properties. | Lead optimization and benchmark validation. |
| **`bionemo_run_benchmark`** | Profiles GPU NIM inference latency, throughput, and CPU baselines. | Performance evaluation, scaling studies, and publication plots. | Generating publication-ready benchmark metrics. |

---

## 4. GitHub MCP Server Tools (`github-mcp-server`)

| Tool Name | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`create_repository`** / **`fork_repository`** | Creates or forks GitHub repositories. | Project setup or open-source contribution setups. | Repository management. |
| **`get_file_contents`** / **`search_code`** | Reads remote files or searches code across GitHub repos. | Code inspection across upstream or external repos. | Remote code exploration. |
| **`create_or_update_file`** / **`push_files`** | Commits files directly to a GitHub repository or branch. | Syncing local progress to remote GitHub branches. | Remote file updates. |
| **`create_branch`** / **`list_commits`** | Creates branches or lists commit history on GitHub. | Preparing features or tracking git provenance. | Branch and commit workflows. |
| **`create_issue`** / **`list_issues`** / **`get_issue`** | Creates, lists, or gets issue tickets on GitHub repositories. | Bug tracking, ticket management, task boards. | Issue management. |
| **`create_pull_request`** / **`get_pull_request`** | Creates and inspects Pull Requests. | Submitting code for review or reviewing teammates' PRs. | PR workflows. |
| **`merge_pull_request`** / **`create_pull_request_review`** | Reviews or merges GitHub PRs. | Automated CI/CD or PR acceptance. | Pull request automation. |

---

## 5. Stitch UI & Design System Tools (`StitchMCP`)

| Tool Name | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`create_project`** / **`get_project`** / **`list_projects`** | Manages UI design projects in Stitch. | Starting a new UI cockpit or frontend app design. | Design project organization. |
| **`generate_screen_from_text`** | Generates UI screen mockups and layout code from textual descriptions. | Designing interactive cockpits (e.g., BioNeMo Cockpit). | Rapid UI prototyping. |
| **`edit_screens`** / **`generate_variants`** | Edits existing UI screens or creates design variants. | Iterating on dark-mode themes, buttons, or charts. | Exploring visual variations. |
| **`create_design_system`** / **`apply_design_system`** | Builds or applies unified design systems across screens. | Ensuring consistent tokens, colors, typography, and spacing. | Design consistency and polish. |

---

## 6. Chrome DevTools MCP Tools (`chrome-devtools-mcp`)

| Tool Name | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`navigate_page`** / **`new_page`** / **`close_page`** | Controls active browser tabs and navigates URLs. | Opening local dev servers (e.g., `localhost:8000`). | Tab lifecycle management. |
| **`click`** / **`type_text`** / **`press_key`** / **`fill_form`** | Interacts with UI buttons, inputs, forms, and keyboard. | Driving end-to-end user workflows automatically. | Interactive web automation. |
| **`take_screenshot`** / **`take_snapshot`** | Captures visual screenshots or accessibility DOM snapshots. | Verifying layout rendering and UI visual regressions. | Visual and accessibility validation. |
| **`evaluate_script`** | Runs custom JavaScript in the live browser page context. | Checking DOM state, localStorage, or custom metric counters. | Runtime client-side inspection. |
| **`lighthouse_audit`** | Runs complete Lighthouse performance, SEO, and a11y audits. | Auditing web apps for Core Web Vitals and accessibility. | Automated quality scoring. |
| **`performance_start_trace`** / **`stop`** | Profiles render performance, frame rates, and script bottlenecks. | Diagnosing slow animations or UI sluggishness. | Performance optimization. |
| **`list_console_messages`** / **`network`** | Inspects browser console errors, warnings, and network traffic. | Debugging API calls, failed fetch requests, or CORS errors. | Frontend debugging. |

---

## 7. Perplexity Research (`perplexity-ask`)

| Tool Name | What It Does | When to Apply | Best For |
| :--- | :--- | :--- | :--- |
| **`perplexity_ask`** | Queries Perplexity AI for synthesized, cited research and web answers. | Fact-checking biological mechanisms, drug targets, or newest NIM releases. | Deep scientific literature and current technical information synthesis. |

---

## 8. Multi-Agent Model Tiering (Token Efficiency Protocol)

| Tier | Role & Scope | Token Saving Strategy |
| :--- | :--- | :--- |
| **Lead Orchestrator** | High-level decomposition, architecture, review, synthesis. | Never ingests massive raw logs or large source files into parent context. |
| **`pro` Tier** | High-reasoning architecture, algorithmic proofs, complex debugging. | Reserved for deep reasoning where lower tiers fail. |
| **`flash` Tier** | Standard workhorse code editing, test creation, refactoring, script execution. | High throughput, minimal latency, cost-effective code generation. |
| **`flash_lite` Tier** | Codebase scanning, grep filtering, quick syntax verifications. | Ultra-low token overhead for reconnaissance. |
