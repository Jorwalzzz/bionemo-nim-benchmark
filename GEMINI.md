# Antigravity Workspace Configuration: NVIDIA BioNeMo & NIM

Domain standards and execution directives for the NVIDIA BioNeMo Benchmark Suite:

## Primary Directives & Invariants
1. **Target Environment**: Python 3.12 managed via `.venv` (`.venv\Scripts\python.exe`).
2. **Automated Verification**: All changes must verify with `.venv\Scripts\python.exe -m pytest -v`. Maintain 100% test hermeticity across all 71 tests.
3. **Biological Validation**: Canonical 20 IUPAC residues required before calling ESMFold/ESM-2 models.
4. **Cheminformatics**: Sanitize all SMILES via RDKit with explicit valence checking.
5. **Security & Credentials**: Keep `NVIDIA_API_KEY` secure in `.env`; maintain `--mock` execution for zero-credit testing.

## Token Efficiency & Engineering Execution Rules
1. **Direct Execution**: No roleplay, personas, or simulated multi-agent dialogue. Respond as a direct senior engineer.
2. **Surgical File Slicing**: Always use line ranges (`StartLine`, `EndLine`) when reading files. Never view entire files.
3. **Atomic Diffs**: Use `replace_file_content` targeting small contiguous blocks. Never rewrite entire files.
4. **Targeted Output**: Format responses strictly: (1) Technical summary of diff, (2) Test status pass/fail, (3) Open questions.
