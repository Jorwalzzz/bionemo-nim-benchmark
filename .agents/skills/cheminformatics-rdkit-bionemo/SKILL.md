---
name: cheminformatics-rdkit-bionemo
description: >-
  Use this skill when processing small molecules, validating SMILES strings, performing RDKit sanitization,
  checking valency/aromaticity, generating 3D conformers, or computing Lipinski Rule of 5 descriptors
  (MW, LogP, TPSA, HBD, HBA) for NVIDIA BioNeMo NIM models like DiffDock, MolMIM, and MegaMolBART.
---

# Cheminformatics with RDKit for BioNeMo

NVIDIA BioNeMo generative chemistry and molecular docking models require structurally sound, chemically valid small molecule inputs.

## Core Capabilities

1. **SMILES Sanitization & Kekulization**:
   - Parses SMILES without initial sanitization to isolate syntax vs chemical valence errors.
   - Applies `Chem.SanitizeMol` with all flags (Kekulization, aromaticity, valence).
   - Generates canonical isomeric SMILES to eliminate non-standard representations.

2. **Physicochemical Descriptors**:
   - Computes Molecular Weight (Exact MolWt).
   - Wildman-Crippen partition coefficient ($\text{LogP}$).
   - Topological Polar Surface Area ($\text{TPSA}$).
   - Hydrogen Bond Donors ($\text{HBD}$) and Acceptors ($\text{HBA}$).
   - Number of Rotatable Bonds (essential for DiffDock torsional search space).

3. **Valency Failure Handling**:
   - Catches hypervalent atoms (e.g. pentavalent carbon, neutral 4-valent nitrogen) gracefully without crashing pipelines.

---

## Python Usage Example

```python
from src.pipeline import BenchmarkPipeline

smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
result = BenchmarkPipeline.sanitize_ligand_smiles(smiles)

if result.is_valid:
    print(f"Canonical SMILES: {result.canonical_smiles}")
    print(f"MW: {result.molecular_weight} g/mol")
    print(f"LogP: {result.log_p}")
    print(f"TPSA: {result.tpsa} A^2")
    print(f"Rotatable Bonds: {result.num_rotatable_bonds}")
else:
    print(f"Invalid molecule: {result.error_message}")
```

---

## Detailed References
- [SMILES Sanitization & Validation Protocol](./references/smiles_sanitization.md): Detailed error classes, edge cases, and RDKit sanitization flags.
