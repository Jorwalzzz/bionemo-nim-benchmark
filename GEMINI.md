# Antigravity Workspace Configuration: NVIDIA BioNeMo & NIM

Domain standards and execution directives for the NVIDIA BioNeMo Benchmark Suite:

## Primary Directives & Invariants
1. **Target Environment**: Python 3.12 managed via `.venv` (`.venv\Scripts\python.exe`).
2. **Automated Verification**: All changes must verify with `.venv\Scripts\python.exe -m pytest -v`. Maintain 100% test hermeticity across all 71 tests.
3. **Biological Validation**: Canonical 20 IUPAC residues required before calling ESMFold/ESM-2 models.
4. **Cheminformatics**: Sanitize all SMILES via RDKit with explicit valence checking.
5. **Security & Credentials**: Keep `NVIDIA_API_KEY` secure in `.env`; maintain `--mock` execution for zero-credit testing.

## Token Efficiency & Engineering Execution Directives
1. **Direct Execution**: Zero roleplay, personas, councils, or simulated dialogue. Respond as a direct senior engineer.
2. **Search-First & Surgical Slicing**: Always use `grep_search` to pinpoint symbols/lines before viewing. Slices must not exceed 100 lines (`StartLine`, `EndLine`). Never view entire files.
3. **Atomic Contiguous Diffs**: Use `replace_file_content` targeting small contiguous blocks. Never rewrite entire files with `write_to_file`.
4. **Terse CLI Execution**: Run commands with quiet flags (`pytest -q --tb=short`, `git status -s`) to prevent log bloat from polluting context.
5. **Deterministic Verification Loop**: Run local tests/syntax checks (`py_compile` or `pytest`) immediately after code changes to catch errors deterministically before ending turns.
6. **Zero Output Filler**: No conversational preamble, no repeating the prompt, no boilerplate. Output strictly: (1) Technical summary of diff, (2) Verification status (pass/fail), (3) Open questions or next action.
