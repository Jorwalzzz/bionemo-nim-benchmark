---
name: macromolecular-pdb-prep
description: >-
  Use this skill when processing macromolecular structures (PDB, mmCIF), extracting canonical 20 IUPAC
  protein amino acid sequences, cleaning heteroatoms/water molecules, generating synthetic backbone
  conformations, or preparing receptors for NVIDIA NIM DiffDock and ESM-2.
---

# Macromolecular Structure Preparation for BioNeMo

NVIDIA BioNeMo endpoints like ESM-2, ESMFold, and DiffDock require clean, standardized representations of protein targets.

## Core Procedures

1. **Amino Acid Sequence Validation**:
   - Must contain only the 20 standard IUPAC amino acids:
     `A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y`.
   - Strip all internal whitespace, newlines, and lowercase formatting.
   - Non-canonical residues (selenocysteine `U`, pyrrolysine `O`, ambiguous `X`, `B`, `Z`) must be rejected or substituted before submission.

2. **PDB Atom Record Sanitization**:
   - Strip crystallographic water molecules (`HOH`, `WAT`) and non-relevant crystallization buffers (`SO4`, `EDO`, `GOL`).
   - Retain only `ATOM` records with valid $N, C\alpha, C, O$ backbone coordinates.

3. **Synthetic Backbone Generation (Fallback)**:
   - When experimental crystal coordinates are unavailable (e.g. sequence-only targets), construct an idealized extended peptide backbone ($N-C\alpha-C$) with standard bond lengths ($1.46\ \text{Å}, 1.52\ \text{Å}$) and angles ($110^\circ, 120^\circ$) to provide valid 3D coordinates to DiffDock.

---

## Python Usage Example

```python
from src.client import NimBioClient
from src.pdb_utils import sanitize_pdb_atom_records, generate_synthetic_backbone

# 1. Validate sequence
raw_sequence = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG\n"
clean_seq = NimBioClient.validate_protein_sequence(raw_sequence)

# 2. Generate fallback structural backbone if PDB is missing
pdb_string = generate_synthetic_backbone(clean_seq)
print(f"Generated {len(pdb_string.splitlines())} lines of PDB structure.")
```

---

## Detailed References
- [PDB Structure Validation & Cleaning Guide](./references/pdb_validation.md): Atom record formatting, handling gaps, and DiffDock receptor expectations.
