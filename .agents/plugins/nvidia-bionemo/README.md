# NVIDIA BioNeMo Accelerated Biology Plugin

This plugin bundles specialized domain capabilities for NVIDIA BioNeMo & NIM microservices into Antigravity IDE:

## Included Capabilities
1. **BioNeMo NIM Client & Inference Workflows**: Endpoints, schemas, rate-limiting, retries, and local Docker deployments for ESM-2, DiffDock, ESMFold, and MolMIM.
2. **Benchmark Profiling**: Calculation of token throughput ($\text{tokens}/\text{sec}$), per-residue latency ($ms/\text{residue}$), GPU speedups, and 300 DPI publication plots.
3. **RDKit Cheminformatics**: Chemical graph validation, SMILES sanitization, valency verification, and Lipinski descriptor calculations.
4. **Macromolecular Prep**: Amino acid sequence validation, PDB atom record cleaning, and synthetic backbone generation.
5. **Native MCP Server (`bionemo-tools`)**: Provides direct agent execution tools for validating sequences, sanitizing SMILES, running benchmarks, and querying NIM endpoints.
