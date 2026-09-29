---
name: target-druggability-assessment
description: Use this skill to evaluate macromolecular binding pocket volume, hydrophobicity, enclosure, and druggability scores before initiating high-throughput molecular docking or generative design campaigns.
---

# Target Druggability Assessment & Pocket Characterization

## Purpose
Before running expensive GPU-docking campaigns with NVIDIA DiffDock or generating libraries with MolMIM, verify that the biological target possesses a tractable, druggable pocket.

## Key Druggability Criteria
A binding pocket is considered druggable if it satisfies the following physicochemical thresholds:

1. **Volume & Depth**:
   - Volume: $300\text{ \AA}^3 \le V \le 1200\text{ \AA}^3$ (accommodates molecules with MW 300–550 Da).
   - Enclosure score: $\ge 0.5$ (concave surface shielding ligands from bulk solvent).

2. **Hydrophobicity & Polarity**:
   - Hydrophobic contact surface area: $40\% – 70\%$.
   - Excessive polarity leads to high desolvation penalties during ligand binding.

3. **Key Catalytic / Interaction Motifs**:
   - Hydrogen-bond donor/acceptor pairs at the active site.
   - Aromatic residues (Phe, Tyr, Trp) for $\pi$-$\pi$ or cation-$\pi$ stacking.

## Workflow
1. **Clean Target Structure**:
   - Strip crystallographic waters, salts, and non-covalent cofactors using `macromolecular-pdb-prep`.
2. **Identify Target Subpocket**:
   - Determine bounding box around catalytic residues (e.g. `Asp-Phe-Gly` DFG motif in kinases, or `Cys145-His41` dyad in SARS-CoV-2 Mpro).
3. **Calculate Druggability Index ($D_{score}$)**:
   - $D_{score} \ge 0.70$: High tractability (proceed with standard screening).
   - $0.50 \le D_{score} < 0.70$: Moderate tractability (covalent or allosteric strategy recommended).
   - $D_{score} < 0.50$: Undruggable / shallow protein-protein interaction (PPI) surface.
