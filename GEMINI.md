# Antigravity Workspace Configuration: NVIDIA BioNeMo & NIM

Welcome to the NVIDIA BioNeMo Benchmark Suite workspace. When operating in this repository, follow these domain-specific standards:

## Priority Workflows
- **Primary Workspace Migrated to Disk D**: All active development, benchmarking, test runs, and pipeline tasks must now be conducted in `D:\BIONEMO` (linked at `D:\Antigravity\BIONEMO`).
- **NVIDIA BioNeMo & NIM Inference**: Use `bionemo-nim-inference` skill and `bionemo-tools` MCP to query ESM-2 protein language models and DiffDock molecular docking.
- **RDKit Cheminformatics**: Use `cheminformatics-rdkit-bionemo` for SMILES parsing, valency verification, and Lipinski descriptor calculations.
- **Macromolecular Prep**: Use `macromolecular-pdb-prep` and `pdb-database` for fetching, cleaning, and validating PDB files.
- **Benchmarking & Profiling**: Use `bionemo-benchmark-profiler` to run benchmarks, calculate speedup, and render 300 DPI publication plots.

## Key Rules
1. Any work regarding BioNeMo should target `D:\BIONEMO`.
2. Validate all amino acid sequences against canonical 20 IUPAC residues before calling ESM-2/DiffDock.
3. Sanitize all SMILES via RDKit with explicit valence checking.
4. Keep `NVIDIA_API_KEY` secure in `.env`; maintain `--mock` execution for zero-credit testing.
5. Manage Python packages via `.venv` and verify changes with `pytest -v`.
6. **Multi-Agent Orchestrator Directive**: Follow `.agents/rules/orchestrator-directive.md` strictly. Act as Lead Architect & Dispatcher, preserve parent context, and route tasks using model tiering (`pro`, `flash`, `flash_lite`).

