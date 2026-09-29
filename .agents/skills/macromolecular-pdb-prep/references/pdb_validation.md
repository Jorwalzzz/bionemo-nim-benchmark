# PDB Structure Validation & Cleaning Reference

## Structure Expectations for NVIDIA NIM DiffDock

1. **Receptor Input**:
   - Standard PDB format containing ATOM records.
   - Residue numbering must correspond to standard protein chains (e.g. Chain A).
   - Each amino acid residue must have at least the primary backbone atoms ($N$, $CA$, $C$, $O$).

2. **Removing Heteroatoms & Solvents**:
   - Solvents like water molecules (`HOH`) distort blind docking energy surfaces and should be removed unless known catalytic waters are required.
   - Non-covalently bound crystal ligands, ions, or detergents should be stripped prior to blind docking.

3. **Coordinate Precision**:
   - PDB coordinate fields use fixed format `F8.3` (orthogonal coordinates in Angstroms).
   - Ensure coordinates contain non-degenerate $(x, y, z)$ positions.
