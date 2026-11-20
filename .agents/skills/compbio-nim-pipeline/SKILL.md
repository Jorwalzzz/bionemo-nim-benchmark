---
name: compbio-nim-pipeline
description: "Enforce computational biology and NVIDIA BioNeMo / NIM engineering standards: strict Python typing, deterministic seeds, FASTA sequence validation, PDB atom record sanitization, RDKit SMILES cheminformatics validation, tmp_path test isolation, and microservice payload integration."
---

# Computational Biology & BioNeMo NIM Pipeline Standards

This skill governs computational biology algorithms, macromolecular sequence and structural handling, chemical informatics, and NVIDIA BioNeMo / NIM microservice integration in the `bionemo-nim-benchmark` codebase.

## 1. Python Typing & Code Discipline
- **Strict Typing:** All function signatures must include exhaustive type annotations from `typing` (`Annotated`, `Callable`, `Sequence`, `Literal`) or standard Python 3.10+ union types (`int | None`).
- **Data Models:** Use typed dataclasses (`@dataclass(frozen=True)`) or Pydantic V2 models (`BaseModel`) for all data transfer objects, benchmark metrics, and API payloads.
- **Explicit Imports:** Disallow wildcard imports (`from module import *`). Use clean, grouped imports (`stdlib`, third-party, local package).

## 2. Determinism & Benchmark Reproducibility
- **Seed Management:** All stochastic operations (clustering, molecular conformer generation, synthetic sequence sampling, mock latency generators) must accept an explicit `seed: int = 42` and configure both `random.seed(seed)` and `np.random.seed(seed)`.
- **Latency Accounting:** Benchmark latency measurements must strictly isolate pure server inference latency from network roundtrip time (RTT). The `NimBioClient` records:
  - `server_inference_latency_s`: Execution time within the NIM container.
  - `network_overhead_s`: RTT - server inference time.
  - `total_wall_clock_s`: End-to-end client duration.

## 3. Macromolecular Sequence Processing (ESM-2 / ESMFold)
- **Canonical IUPAC Amino Acids:** Validate all protein sequences against the standard 20 single-letter IUPAC amino acid alphabet:
  ```python
  CANONICAL_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")
  ```
- **Validation Protocol:**
  - Strip whitespace, FASTA header lines (`>...`), and terminal stop codons (`*`).
  - Convert to uppercase.
  - Validate that every character is in `CANONICAL_AMINO_ACIDS`.
  - Calculate estimated molecular weight: $\text{MW}_{\text{kDa}} \approx \frac{\text{len}(\text{seq}) \times 110.0}{1000.0}$.

## 4. Structural Biology & PDB Sanitation (DiffDock / ESMFold)
- **PDB Record Formatting:** PDB atom records must adhere strictly to the 80-column standard format:
  `ATOM  / HETATM | atom_num (6-11) | atom_name (13-16) | altLoc (17) | resName (18-20) | chainID (22) | resSeq (23-26) | x (31-38) | y (39-46) | z (47-54) | occ (55-60) | temp (61-66) | elem (77-78)`
- **Sanitization Requirements:**
  - Remove redundant water molecules (`HOH`, `WAT`) unless performing explicit solvent docking.
  - Ensure unique atom serial numbers and correct coordinate precision (`.3f`).
  - Compute AlphaFold / ESMFold pLDDT confidence metrics:
    - $\text{pLDDT} \ge 90$: Very high confidence (blue / `#5CE1FF`).
    - $70 \le \text{pLDDT} < 90$: High confidence (green / `#76F5A2`).
    - $50 \le \text{pLDDT} < 70$: Low confidence (amber / `#FF8A4C`).
    - $\text{pLDDT} < 50$: Very low confidence (red / `#EF4444`).

## 5. Cheminformatics & SMILES Validation (MolMIM / DiffDock)
- **RDKit Validation:**
  - Validate every SMILES string using `Chem.MolFromSmiles(smiles, sanitize=True)`.
  - Check for valence violations, Kekulization errors, and unclosed rings.
  - Compute Lipinski Rule of 5 descriptors: Molecular Weight ($\le 500\text{ Da}$), LogP ($\le 5$), H-Bond Donors ($\le 5$), H-Bond Acceptors ($\le 10$), TPSA ($\le 140\text{ \AA}^2$).
- **Graceful Fallback:** When RDKit is not installed in lightweight testing environments, use fallback regex-based formula estimators and clearly log that exact chemical descriptors require RDKit.

## 6. Test Suite Isolation & Hermeticity
- **No Workspace Pollution:** Unit tests must never create unmanaged temporary files in the repository root or system temp without cleanup. Always inject pytest's `tmp_path` fixture.
- **Hermetic Mocking:** Network calls to NVIDIA NIM endpoints (`integrate.api.nvidia.com`) must be mocked with realistic payload fixtures during unit and regression testing.
