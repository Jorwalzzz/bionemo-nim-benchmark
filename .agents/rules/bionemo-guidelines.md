# NVIDIA BioNeMo & NIM Accelerated Biology Guidelines

This ruleset governs bioinformatics and cheminformatics workflows involving NVIDIA BioNeMo, NVIDIA NIM microservices, RDKit, and high-performance molecular modeling.

## 1. Sequence & Chemical Structure Integrity
- **Protein Sequences**:
  - Always validate sequences against the 20 canonical IUPAC amino acids: `ACDEFGHIKLMNPQRSTVWY`.
  - Strip whitespace, carriage returns, and uppercase all sequence strings.
  - Reject non-canonical amino acids (e.g. `X`, `B`, `Z`, `U`) before dispatching to ESM-2 or DiffDock to prevent remote API crashes.
- **Small Molecule Ligands**:
  - Parse and sanitize all SMILES strings using RDKit (`Chem.SanitizeMol`) before downstream inference.
  - Verify explicit valence (e.g., hypervalent nitrogens or pentavalent carbons must fail validation gracefully).
  - Always export canonical isomeric SMILES for consistent docking and embedding reproducibility.

## 2. NVIDIA NIM & BioNeMo API Architecture
- **Credential Safety**:
  - Store and load `NVIDIA_API_KEY` strictly via `.env` or system environment variables. Never commit or print API keys in logs or artifacts.
- **Rate-Limiting & Retries**:
  - Implement exponential backoff with jitter on HTTP 429 (Rate Limit) and 5xx errors.
  - Differentiate between network round-trip overhead and actual GPU inference time (`server_inference_ms`).
- **Mock Simulation Fallback**:
  - Maintain a mock simulation mode for all client calls so that test suites, CI/CD pipelines, and local development can run without requiring active cloud API credits.

## 3. HPC Benchmarking & Metrics
- **Metric Definitions**:
  - Token Throughput: $\text{tokens}/\text{sec} = \frac{\text{sequence\_length}}{\text{latency\_sec}}$
  - Per-Residue Latency: $ms/\text{residue} = \frac{\text{total\_latency\_ms}}{\text{sequence\_length}}$
  - Speedup Factor: $\frac{\text{CPU\_Latency}}{\text{NIM\_Latency}}$
- **Visualizations**:
  - Generate 300 DPI charts stored in `results/` using Seaborn darkgrid/whitegrid styles.
  - Label both axes with exact biological and computational units ($ms$, $\text{tokens}/\text{sec}$, $\text{kcal}/\text{mol}$).

## 4. Environment & Testing
- Use `.venv` with `uv` for python dependencies.
- Ensure all tests pass via `pytest -v` prior to completing bioinformatics pipeline modifications.
