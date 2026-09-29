# SMILES Sanitization & Chemical Validation Reference

## Common RDKit Failure Modes in Biological Workflows

### 1. Hypervalent Nitrogen / Valency Errors
- **Example**: `CN(C)(C)(C)C` (Neutral nitrogen with 5 single bonds).
- **Diagnosis**: Nitrogen can only form 3 covalent bonds (neutral) or 4 covalent bonds (quaternary cation with `+` formal charge).
- **Handling**: RDKit raises `ValueError: Explicit valence for atom # 1 N, 5, is greater than permitted 3`. The pipeline captures this in `error_message` and marks `is_valid=False`.

### 2. Aromaticity & Kekulization Failures
- **Example**: Lowercase atoms in non-aromatic cycles (e.g. `c1cccc1`).
- **Diagnosis**: 5-membered carbon cycle has 5 $\pi$ electrons, violating Hückel's rule ($4n+2$).
- **Handling**: `Chem.SanitizeMol` fails Kekulization.

### 3. Rotatable Bond Considerations for DiffDock
DiffDock diffusion runs over the continuous group $SE(3) \times SO(3)^m$, where $m$ is the number of rotatable bonds. Molecules with $> 12$ rotatable bonds have exponentially larger conformational search spaces and benefit from increased inference steps (e.g. `steps=20` or higher).
