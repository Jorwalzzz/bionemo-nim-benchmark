# Antigravity Token Waste Elimination Protocol

## 1. Simplicity-First (Anti-Overengineering)
- If a clean, focused 20-30 line function or script solves the user's task, never create complex abstraction layers, multiple helper classes, or unnecessary configuration boilerplate.
- Prefer minimal, high-leverage modifications over sprawling rewrites.

## 2. Surgical File Slicing Mandatory
- Never view or print whole source files when inspecting code.
- Always supply StartLine and EndLine to iew_file to keep token consumption bounded to the precise region of interest. Saves 80-85% of input tokens.

## 3. Terminal Traceback Filtering
- When executing command-line tests (e.g. pytest), never dump hundreds of raw lines of output into the conversation.
- Use quiet/compact flags (pytest -q --tb=short) and extract only the relevant failing lines and traceback assertions.

## 4. Atomic In-Place Diffs
- Always use 
eplace_file_content or multi_replace_file_content targeting exact anchors rather than overwriting entire files with write_to_file.
- Cuts expensive output token generation by 80-90%.

## 5. Zero Conversational Fluff
- Deliver direct, actionable responses formatted in clean GitHub markdown.
- Never repeat or re-summarize entire artifact contents in chat messages; provide concise pointers and highlights.

## 6. Reactive Wakeup Over Busy Polling
- Never execute busy-polling loops or sleep commands while waiting for long-running processes or background subagents.
- Let the Antigravity reactive event system wake up the context when events conclude.

## 7. Universal 200-Token Sub-Agent Output Ceiling
- Every specialist sub-agent must strictly cap its inter-agent report under 200 tokens.
- This creates the ideal "Goldilocks Zone": leaves ample room for complete file paths, CLI flags, and metric scores without triggering truncated thoughts or conversational filler.
- NEXUS-PRIME rejects any sub-agent report exceeding 200 tokens, enforcing structured 3-to-4 bullet scorecards.

