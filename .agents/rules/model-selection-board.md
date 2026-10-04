# Antigravity Model Selection Board & Fallback Routing Protocol

## 1. Model Selection Board
Before routing a task or launching a subagent, the 3-member Board evaluates the assignment against three primary dimensions:

| Member / Criterion | Evaluation Factor | Primary Model Assigned | Rationale |
| :--- | :--- | :--- | :--- |
| **Logic & Depth Judge** | Deep reasoning, novel algorithms, multi-hop debugging, security architecture. | **Claude Opus 5.5** or **Gemini 3.1 Pro** | Highest cognitive depth; prevents regression loops on difficult problems. |
| **Execution & Speed Judge** | High-velocity implementation, unit tests, refactoring, batch script runs. | **Gemini 3.8 Flash** | Maximum token efficiency, instantaneous response, lowest latency. |
| **Aesthetics & Clarity Judge** | Modern UI styling, glassmorphism, clean typed interfaces, frontend polish. | **Claude Sonnet 5.5** | Unmatched CSS/design system generation and readable architecture. |

---

## 2. Workflow Fallback & Rate-Limit Switching Matrix
If a model encounters a rate limit (HTTP 429), quota exhaustion, or degraded API response, the Workflow Switcher automatically diverts the prompt to the secondary and tertiary alternatives:

| Primary Model | Secondary Fallback | Tertiary Emergency Path | Failover Strategy |
| :--- | :--- | :--- | :--- |
| **Gemini 3.8 Flash** | Gemini 3.7 Flash | Gemini 3.6 Flash | Instant swap; keeps speed & low token cost intact. |
| **Claude Sonnet 5.5** | Gemini 3.8 Flash | Claude Opus 5.5 | Preserves clean code structure while maintaining velocity. |
| **Claude Opus 5.5** | Gemini 3.1 Pro | Claude Sonnet 5.5 | Keeps deep reasoning capability active without halting workflows. |
| **Gemini 3.1 Pro** | Claude Opus 5.5 | Gemini 3.8 Flash (High) | Transfers multi-hop graph analysis to secondary reasoning model. |

---

## 3. Token Efficiency Optimization During Multi-Agent Operations
Even with a full council of subagents, token burn is strictly minimized via:
1. **Isolated Execution Contexts**: Each subagent runs in its own sandbox; only concise structured diffs and 4-point summaries return to the council.
2. **Zero Chatter Rule**: Inter-agent communication is restricted to markdown key-value reports. No polite filler, no duplicated logs.
3. **Line-Bounded Tool Calls**: All file inspections by any subagent MUST use line ranges (StartLine/EndLine).
