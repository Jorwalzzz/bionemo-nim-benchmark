# Drug Candidate Selection Dossier: ESMFold: De Novo Variant
**Target:** ESMFold: De Novo Variant (DE_NOVO) | **UniProt:** ESMFOLD | **PDB:** ESMF  
**Date of Selection:** 2026-09-29 05:36:31 UTC  
**Principal Investigator:** Agentic BioNeMo Autonomous Discovery System  

---

## 1. Executive Summary & Clinical Rationale
Targeting oncogenic **ESMFold: De Novo Variant** represents a transformative therapeutic avenue in clinical oncology. 
De novo atomic 3D structure predicted by NVIDIA NIM ESMFold from primary sequence (Mean pLDDT: 89.7%).

Using an autonomous closed-loop agentic workflow powered by **NVIDIA NIM MolMIM**, **RDKit ADMET screening**, and **NVIDIA NIM DiffDock**, we screened 3 bioisosteric derivatives of reference scaffold **Bioisosteric Core Scaffold**.

### Key Discovery Highlights:
- **Nominated Lead:** `NIM-LEAD-01-01`
- **Predicted Binding Free Energy ($\Delta G$):** **-9.92 kcal/mol**
- **Drug-likeness (QED):** **0.614** (Complies with Lipinski Rule of 5)
- **Synthetic Accessibility Score:** **5.88 / 10**
- **Target Pocket Residue Contacts:** Glu600, Lys483

---

## 2. Top Lead Candidates Ranked by Multi-Objective Pareto Frontier

| Lead ID | SMILES | $\Delta G$ (kcal/mol) | QED | MW (g/mol) | LogP | SAScore | Pareto? | ADMET Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NIM-LEAD-01-01** | `COC1=C(OCC2CCNCC2)C=C3C(=C1)...` | **-9.92** | 0.614 | 416.9 | 4.55 | 5.88 | ★ YES | `PASS` |
| **NIM-LEAD-01-02** | `COC1=C(OCC2CCOCC2)C=C3C(=C1)...` | **-9.77** | 0.610 | 417.9 | 4.98 | 5.89 | No | `PASS` |
| **NIM-LEAD-01-03** | `COC1=C(OCC2CCN(C)CC2)C=C3C(=...` | **-9.75** | 0.600 | 430.9 | 4.90 | 5.93 | No | `PASS` |

---

## 3. ADMET & Liability Assessment
- **Blood-Brain Barrier (BBB) Permeability:** 0 of top 3 leads meet CNS permeability heuristics.
- **Cardiotoxicity (hERG Alert):** 0 flagged liabilities.
- **PAINS Motifs:** 0 reactive or assay-interfering sub-structures in final leads.

---

## 4. Recommended Experimental Next Steps (In Vitro & In Vivo)
1. **Chemical Synthesis**: Solubilization and solid-phase synthesis targeting the core scaffold of `NIM-LEAD-01-01`.
2. **Biophysical Validation**: Surface Plasmon Resonance (SPR) and Microscale Thermophoresis (MST) to determine $K_D$ dissociation constant against recombinant ESMFold: De Novo Variant.
3. **Cellular Target Engagement**: NanoBRET cellular kinase binding assay in mutant cell line.

---

## 🧬 Pipeline Architecture & Acknowledgements
- **Architected and Engineered by**: [Jorwalzzz](https://github.com/Jorwalzzz)
- **Generative Molecular Modeling & Docking**: Accelerated via NVIDIA BioNeMo™ & NIM™ microservices (MolMIM, DiffDock, ESM-2).
- **Cheminformatics & Structural Foundations**: Powered by RDKit, RCSB Protein Data Bank, and 3Dmol.js.
