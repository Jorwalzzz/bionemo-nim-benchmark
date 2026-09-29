---
name: bionemo-esmfold-generation
description: Use this skill when predicting atomic-resolution 3D macromolecular structures from raw protein sequences using NVIDIA BioNeMo ESMFold NIM. Covers pLDDT extraction, per-residue confidence evaluation, and structure export for docking.
---

# NVIDIA BioNeMo ESMFold NIM Structure Prediction

## Overview
NVIDIA NIM ESMFold predicts accurate 3D atomic coordinates directly from primary amino acid sequences in single-digit seconds, bypassing MSA (Multiple Sequence Alignment) search latency.

## Prerequisites & Validation
1. **Sequence Sanitization**:
   - Must contain only the canonical 20 IUPAC amino acid residues (`ACDEFGHIKLMNPQRSTVWY`).
   - Strip any leading FASTA header (`>sp|...`) or whitespace.
   - Ideal length: $\le 1000$ amino acids (split longer sequences into functional domains).

2. **NVIDIA NIM Endpoint Configuration**:
   - Cloud Endpoint: `https://health.api.nvidia.com/v1/biology/meta/esmfold`
   - Headers:
     ```json
     {
       "Authorization": "Bearer $NVIDIA_API_KEY",
       "Content-Type": "application/json",
       "Accept": "application/json"
     }
     ```
   - Payload:
     ```json
     {
       "sequence": "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQ"
     }
     ```

## Assessing Model Confidence (pLDDT)
The predicted PDB structure stores the per-residue confidence score in the **B-factor column**:
- **pLDDT > 90**: Very high confidence (reliable sidechain and backbone coordinates).
- **70 < pLDDT <= 90**: Confident backbone (suitable for binding pocket detection).
- **50 < pLDDT <= 70**: Low confidence (caution warranted).
- **pLDDT < 50**: Unstructured / intrinsically disordered region (IDR); discard for binding pocket definition.

## Chaining with DiffDock
1. Predict 3D structure via ESMFold NIM.
2. Filter residues with $\text{pLDDT} \ge 70$.
3. Pass resulting PDB content directly into `bionemo_query_diffdock` alongside candidate ligand SMILES.
