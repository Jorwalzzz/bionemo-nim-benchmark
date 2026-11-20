/**
 * BioNeMo NIM Inference Benchmark - Verified RCSB PDB Target Presets
 * Module: ./js/data/target-presets.js
 * 
 * Provides verified macromolecular receptor definitions, bound ligand coordinates,
 * pocket interaction residue indices, and illustrative physicochemical/ADMET profiles
 * across 16 benchmark complexes categorized into 4 therapeutic domains.
 *
 * Epistemic Status:
 * - Structural & Resolution Data: Empirical (RCSB PDB Primary Citations)
 * - Reference SMILES & Topology: RDKit Canonical Sanitized Representation
 * - Predicted Affinity & ADMET: Illustrative In Silico Modeling Profiling
 */

const TARGET_PRESETS_DATA = [
  // =========================================================================
  // CATEGORY 1: REPO BENCHMARK CORE (5 TARGETS)
  // =========================================================================
  {
    id: '7RPZ',
    pdbId: '7RPZ',
    name: 'KRAS G12D (Switch-II Pocket)',
    gene: 'KRAS',
    mutation: 'G12D',
    category: 'Repo Benchmark Core',
    resolutionA: 1.30,
    ligandName: 'MRTX1133',
    ligandCcd: '7RP',
    pocketName: 'Switch-II Pocket (G12D Induced Subpocket)',
    pocketResidues: ['Asp12', 'Gly13', 'Val14', 'Glu62', 'His95', 'Tyr96', 'Gln99'],
    modality: 'Small Molecule Inhibitor (Non-Covalent)',
    referenceSmiles: 'CC1CN(CCN1)c2nc(c3cc(c(cc3n2)F)C#N)Nc4ccc(c(c4)F)N5CCCNCC5',
    affinity: {
      kd_nm: 0.2,
      ic50_nm: 5.0,
      delta_g_kcal_mol: -12.4,
      bindingClass: 'Sub-nanomolar Non-Covalent'
    },
    admet: {
      mw_da: 478.55,
      logp: 3.12,
      tpsa_a2: 92.14,
      hbd: 3,
      hba: 8,
      rotatableBonds: 4,
      caco2Permeability: 'Moderate',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'Non-penetrant'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '4MNE',
    pdbId: '4MNE',
    name: 'BRAF V600E (Kinase Domain)',
    gene: 'BRAF',
    mutation: 'V600E',
    category: 'Repo Benchmark Core',
    resolutionA: 2.10,
    ligandName: 'Vemurafenib',
    ligandCcd: '04I',
    pocketName: 'ATP-Binding C-Helix Pocket (DFG-In Active Conformation)',
    pocketResidues: ['Glu501', 'Leu514', 'Ile527', 'Phe583', 'Gly593', 'Phe595', 'Glu600'],
    modality: 'Type I 1/2 Kinase Inhibitor',
    referenceSmiles: 'CCCS(=O)(=O)Nc1ccc(c(c1)F)C(=O)c2c[nH]c3c2cc(cn3)c4ccc(cc4)Cl',
    affinity: {
      kd_nm: 13.0,
      ic50_nm: 31.0,
      delta_g_kcal_mol: -10.8,
      bindingClass: 'Selective Mutant Inhibitor'
    },
    admet: {
      mw_da: 471.94,
      logp: 5.41,
      tpsa_a2: 91.92,
      hbd: 2,
      hba: 4,
      rotatableBonds: 5,
      caco2Permeability: 'High',
      clearanceRisk: 'Moderate',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '2HYY',
    pdbId: '2HYY',
    name: 'BCR-ABL1 (Kinase Domain)',
    gene: 'ABL1',
    mutation: 'Wild-Type / BCR-ABL1 Fusion',
    category: 'Repo Benchmark Core',
    resolutionA: 2.40,
    ligandName: 'Imatinib',
    ligandCcd: 'STI',
    pocketName: 'ATP-Binding C-Helix / DFG-Out Allosteric Pocket',
    pocketResidues: ['Leu248', 'Tyr253', 'Thr315', 'Met318', 'Ile360', 'Asp381', 'Phe382'],
    modality: 'Type II Kinase Inhibitor',
    referenceSmiles: 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C',
    affinity: {
      kd_nm: 38.0,
      ic50_nm: 250.0,
      delta_g_kcal_mol: -10.1,
      bindingClass: 'Type II Inactive State'
    },
    admet: {
      mw_da: 493.62,
      logp: 4.59,
      tpsa_a2: 86.28,
      hbd: 2,
      hba: 7,
      rotatableBonds: 7,
      caco2Permeability: 'High',
      clearanceRisk: 'Moderate',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '3IKA',
    pdbId: '3IKA',
    name: 'EGFR T790M (Gatekeeper Mutant)',
    gene: 'EGFR',
    mutation: 'T790M',
    category: 'Repo Benchmark Core',
    resolutionA: 2.60,
    ligandName: 'WZ4002',
    ligandCcd: '3IK',
    pocketName: 'ATP Pocket (Met790 Steric Accommodation & Cys797 Adduct)',
    pocketResidues: ['Leu718', 'Val726', 'Lys745', 'Met790', 'Gln791', 'Met793', 'Cys797'],
    modality: 'Covalent / Irreversible EGFR Inhibitor',
    referenceSmiles: 'C=CC(=O)Nc1cc(Nc2ncc(Cl)c(Nc3cccc(C(=O)N4CCN(C)CC4)c3)n2)c(OC)cc1',
    affinity: {
      kd_nm: 8.0,
      ic50_nm: 12.0,
      delta_g_kcal_mol: -11.0,
      bindingClass: 'Covalent Irreversible Inhibitor'
    },
    admet: {
      mw_da: 522.01,
      logp: 4.14,
      tpsa_a2: 111.72,
      hbd: 3,
      hba: 8,
      rotatableBonds: 6,
      caco2Permeability: 'Moderate',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'Non-penetrant'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '1DHF',
    pdbId: '1DHF',
    name: 'Human DHFR (Folate Binding Cleft)',
    gene: 'DHFR',
    mutation: 'Wild-Type',
    category: 'Repo Benchmark Core',
    resolutionA: 2.30,
    ligandName: 'Folate',
    ligandCcd: 'FOL',
    pocketName: 'Pteridine Catalytic Binding Cleft',
    pocketResidues: ['Ile7', 'Glu30', 'Phe31', 'Phe34', 'Leu67', 'Arg70', 'Val115'],
    modality: 'Enzyme Substrate / Competitive Antimetabolite',
    referenceSmiles: 'Nc1nc2ncc(CNc3ccc(C(=O)NC(CCC(=O)O)C(=O)O)cc3)nc2c(=O)[nH]1',
    affinity: {
      kd_nm: 15.0,
      ic50_nm: 40.0,
      delta_g_kcal_mol: -10.7,
      bindingClass: 'Competitive Substrate-Site Binder'
    },
    admet: {
      mw_da: 441.40,
      logp: -0.04,
      tpsa_a2: 213.28,
      hbd: 6,
      hba: 9,
      rotatableBonds: 8,
      caco2Permeability: 'Low',
      clearanceRisk: 'Renal',
      bloodBrainBarrier: 'Non-penetrant'
    },
    epistemicTag: 'Illustrative'
  },

  // =========================================================================
  // CATEGORY 2: ONCOLOGY KINASES (4 TARGETS)
  // =========================================================================
  {
    id: '3PP0',
    pdbId: '3PP0',
    name: 'HER2/ERBB2 (Kinase Domain)',
    gene: 'ERBB2',
    mutation: 'Wild-Type',
    category: 'Oncology Kinases',
    resolutionA: 2.25,
    ligandName: 'SYR127063',
    ligandCcd: '032',
    pocketName: 'Tyrosine Kinase Hinge & Hydrophobic Pouch',
    pocketResidues: ['Leu726', 'Val734', 'Ala751', 'Lys753', 'Met801', 'Thr862', 'Asp863'],
    modality: 'Dual EGFR/HER2 Kinase Inhibitor',
    referenceSmiles: 'Fc1ccccc1Cn1ncc2cc(Nc3nccn4cccc34)ccc21',
    affinity: {
      kd_nm: 6.2,
      ic50_nm: 17.0,
      delta_g_kcal_mol: -11.2,
      bindingClass: 'Nanomolar Type I Kinase Inhibitor'
    },
    admet: {
      mw_da: 357.39,
      logp: 4.62,
      tpsa_a2: 47.15,
      hbd: 1,
      hba: 3,
      rotatableBonds: 3,
      caco2Permeability: 'High',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'Moderate'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '4CLI',
    pdbId: '4CLI',
    name: 'ALK (Kinase Domain)',
    gene: 'ALK',
    mutation: 'Wild-Type / G1202R Resistant Pocket',
    category: 'Oncology Kinases',
    resolutionA: 1.90,
    ligandName: 'Lorlatinib',
    ligandCcd: '27O',
    pocketName: 'Macrocyclic Kinase Hinge Pocket (G1202R Accommodating)',
    pocketResidues: ['Leu1122', 'Val1130', 'Lys1150', 'Met1199', 'Leu1256', 'Asp1270'],
    modality: 'Macrocyclic CNS-Penetrant Type I Kinase Inhibitor',
    referenceSmiles: 'CC1Oc2ccc(C#N)cc2C(=O)N2CCN(CC2)Cc2cc(F)c(c(Cl)c2)O1',
    affinity: {
      kd_nm: 0.7,
      ic50_nm: 1.3,
      delta_g_kcal_mol: -12.5,
      bindingClass: 'Sub-nanomolar Macrocycle'
    },
    admet: {
      mw_da: 415.85,
      logp: 3.43,
      tpsa_a2: 65.80,
      hbd: 0,
      hba: 5,
      rotatableBonds: 1,
      caco2Permeability: 'High',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'High CNS Penetrant'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '4JPS',
    pdbId: '4JPS',
    name: 'PI3Kα (Lipid Kinase Cleft)',
    gene: 'PIK3CA',
    mutation: 'Wild-Type / Oncogenic H1047R Cavity',
    category: 'Oncology Kinases',
    resolutionA: 2.20,
    ligandName: 'Alpelisib',
    ligandCcd: '1E8',
    pocketName: 'Lipid Kinase ATP Cleft (Gln859/His855 Subpocket)',
    pocketResidues: ['Ser774', 'Trp780', 'Ile800', 'Glu849', 'Val850', 'His855', 'Gln859'],
    modality: 'Class I Alpha-Selective PI3K Inhibitor',
    referenceSmiles: 'CC(C)(C)c1nc(NC(=O)N2CCCC2C(=O)O)sc1-c1ccnc(C)n1',
    affinity: {
      kd_nm: 4.6,
      ic50_nm: 5.0,
      delta_g_kcal_mol: -11.4,
      bindingClass: 'Isoform-Selective Lipid Kinase Inhibitor'
    },
    admet: {
      mw_da: 389.48,
      logp: 3.29,
      tpsa_a2: 108.31,
      hbd: 2,
      hba: 6,
      rotatableBonds: 4,
      caco2Permeability: 'Moderate',
      clearanceRisk: 'Moderate',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '5P9J',
    pdbId: '5P9J',
    name: 'BTK (Kinase Domain)',
    gene: 'BTK',
    mutation: 'Wild-Type',
    category: 'Oncology Kinases',
    resolutionA: 1.50,
    ligandName: 'Ibrutinib',
    ligandCcd: '0LI',
    pocketName: 'BTK ATP Pocket & Cys481 Covalent Adduct Site',
    pocketResidues: ['Leu408', 'Val416', 'Ala428', 'Lys430', 'Met477', 'Cys481', 'Asp539'],
    modality: 'Irreversible Covalent Kinase Inhibitor',
    referenceSmiles: 'C=CC(=O)N1CCCC(n2nc(-c3ccc(Oc4ccccc4)cc3)c4c(N)ncnc42)C1',
    affinity: {
      kd_nm: 0.5,
      ic50_nm: 0.5,
      delta_g_kcal_mol: -12.7,
      bindingClass: 'Sub-nanomolar Covalent Adduct'
    },
    admet: {
      mw_da: 440.51,
      logp: 4.22,
      tpsa_a2: 99.16,
      hbd: 1,
      hba: 6,
      rotatableBonds: 5,
      caco2Permeability: 'High',
      clearanceRisk: 'Hepatic (CYP3A4)',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },

  // =========================================================================
  // CATEGORY 3: CELL CYCLE & PPI (4 TARGETS)
  // =========================================================================
  {
    id: '5L2I',
    pdbId: '5L2I',
    name: 'CDK6 (Cyclin D3 Complex)',
    gene: 'CDK6',
    mutation: 'Wild-Type',
    category: 'Cell Cycle & PPI',
    resolutionA: 2.15,
    ligandName: 'Palbociclib',
    ligandCcd: '707',
    pocketName: 'CDK4/6 Catalytic Cleft (ATP Competitive Hinge Interface)',
    pocketResidues: ['Ile19', 'Val77', 'Lys43', 'Phe93', 'His100', 'Val101', 'Asp163'],
    modality: 'Selective CDK4/6 Dual Inhibitor',
    referenceSmiles: 'CC(=O)c1c(C)n(C2CCCC2)c3ncc(Nc4ccc(nc4)N5CCNCC5)nc13',
    affinity: {
      kd_nm: 9.0,
      ic50_nm: 11.0,
      delta_g_kcal_mol: -11.0,
      bindingClass: 'Selective Cell Cycle Inhibitor'
    },
    admet: {
      mw_da: 419.53,
      logp: 3.61,
      tpsa_a2: 87.97,
      hbd: 2,
      hba: 7,
      rotatableBonds: 4,
      caco2Permeability: 'High',
      clearanceRisk: 'Moderate',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '6O0K',
    pdbId: '6O0K',
    name: 'BCL-2 (Anti-Apoptotic BH3 Groove)',
    gene: 'BCL2',
    mutation: 'Wild-Type',
    category: 'Cell Cycle & PPI',
    resolutionA: 1.62,
    ligandName: 'Venetoclax',
    ligandCcd: 'M89',
    pocketName: 'BH3-Mimetic Hydrophobic Groove (P2/P4 Hot-spots)',
    pocketResidues: ['Phe104', 'Arg107', 'Tyr108', 'Phe112', 'Val148', 'Glu152', 'Phe153'],
    modality: 'Protein-Protein Interaction (PPI) Disruptor / BH3 Mimetic (bRo5)',
    referenceSmiles: 'CC1(C)CCC(CN2CCN(c3ccc(C(=O)NS(=O)(=O)c4ccc(NCC5CCOCC5)c([N+](=O)[O-])c4)cc3)CC2)=C(c2ccc(Cl)cc2)C1',
    affinity: {
      kd_nm: 0.010,
      ic50_nm: 0.080,
      delta_g_kcal_mol: -15.1,
      bindingClass: 'Picomolar PPI Disruptor'
    },
    admet: {
      mw_da: 736.34,
      logp: 6.99,
      tpsa_a2: 134.12,
      hbd: 2,
      hba: 9,
      rotatableBonds: 9,
      caco2Permeability: 'Moderate',
      clearanceRisk: 'CYP3A4',
      bloodBrainBarrier: 'Non-penetrant (bRo5)'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '5DS3',
    pdbId: '5DS3',
    name: 'PARP1 (Catalytic Domain)',
    gene: 'PARP1',
    mutation: 'Wild-Type',
    category: 'Cell Cycle & PPI',
    resolutionA: 2.20,
    ligandName: 'Olaparib',
    ligandCcd: 'AZD',
    pocketName: 'NAD+ Catalytic Pocket (Nicotinamide-Mimicking Site)',
    pocketResidues: ['His862', 'Gly863', 'Ser864', 'Arg878', 'Tyr896', 'Phe897', 'Glu988'],
    modality: 'Catalytic PARP Inhibitor & Allosteric Trapping Agent',
    referenceSmiles: 'O=C1Nc2ccccc2C(=O)N1Cc3cc(F)ccc3C(=O)N4CCN(C(=O)C5CC5)CC4',
    affinity: {
      kd_nm: 5.0,
      ic50_nm: 5.0,
      delta_g_kcal_mol: -11.3,
      bindingClass: 'Synthetic Lethality Inhibitor'
    },
    admet: {
      mw_da: 450.47,
      logp: 1.57,
      tpsa_a2: 95.48,
      hbd: 1,
      hba: 4,
      rotatableBonds: 4,
      caco2Permeability: 'Moderate',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '5J89',
    pdbId: '5J89',
    name: 'PD-L1 Dimer (Immune Checkpoint)',
    gene: 'CD274',
    mutation: 'Wild-Type',
    category: 'Cell Cycle & PPI',
    resolutionA: 1.70,
    ligandName: 'BMS-202',
    ligandCcd: '6U0',
    pocketName: 'Induced Hydrophobic Tunnel at PD-L1 Homodimer Interface',
    pocketResidues: ['Ile54', 'Tyr56', 'Met115', 'Ala121', 'Asp122', 'Tyr123', 'Lys124'],
    modality: 'Small Molecule Immune Checkpoint / Dimerization Inducer',
    referenceSmiles: 'COc1ccccc1CCOc2cc(C)cc(C)c2CNCCNC(=O)c3ccccc3',
    affinity: {
      kd_nm: 18.0,
      ic50_nm: 50.0,
      delta_g_kcal_mol: -10.5,
      bindingClass: 'Homodimerization Stabilizer'
    },
    admet: {
      mw_da: 432.56,
      logp: 4.45,
      tpsa_a2: 59.59,
      hbd: 2,
      hba: 4,
      rotatableBonds: 9,
      caco2Permeability: 'High',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'Non-penetrant'
    },
    epistemicTag: 'Illustrative'
  },

  // =========================================================================
  // CATEGORY 4: INFECTIOUS DISEASE (3 TARGETS)
  // =========================================================================
  {
    id: '7VH8',
    pdbId: '7VH8',
    name: 'SARS-CoV-2 Mpro (Main Protease)',
    gene: 'Mpro / 3CLpro',
    mutation: 'Wild-Type',
    category: 'Infectious Disease',
    resolutionA: 1.60,
    ligandName: 'Nirmatrelvir',
    ligandCcd: '4WI',
    pocketName: 'Catalytic Dyad (Cys145-His41) & P1-P4 Subsites',
    pocketResidues: ['Thr25', 'His41', 'Met49', 'Phe140', 'Cys145', 'His163', 'Glu166'],
    modality: 'Covalent Peptidomimetic Nitrile Protease Inhibitor',
    referenceSmiles: 'CC(C)(C)C(NC(=O)C(F)(F)F)C(=O)N1CC2C(C1)C2(C)C(=O)NC(CC3CCNC3=O)C#N',
    affinity: {
      kd_nm: 3.1,
      ic50_nm: 19.0,
      delta_g_kcal_mol: -11.6,
      bindingClass: 'Nanomolar Covalent Protease Inhibitor'
    },
    admet: {
      mw_da: 485.51,
      logp: 0.71,
      tpsa_a2: 131.40,
      hbd: 3,
      hba: 5,
      rotatableBonds: 6,
      caco2Permeability: 'Moderate (P-gp substrate)',
      clearanceRisk: 'Moderate (Ritonavir boosted)',
      bloodBrainBarrier: 'Non-penetrant'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '7BV2',
    pdbId: '7BV2',
    name: 'SARS-CoV-2 RdRp (nsp12-nsp7-nsp8 Complex)',
    gene: 'nsp12',
    mutation: 'Wild-Type',
    category: 'Infectious Disease',
    resolutionA: 2.50,
    ligandName: 'Remdesivir',
    ligandCcd: 'F86',
    pocketName: 'NTP-Addition Catalytic Cavity (Ser759-Asp760 Motifs)',
    pocketResidues: ['Lys545', 'Arg555', 'Asp618', 'Ser759', 'Asp760', 'Asp761', 'Cys813'],
    modality: 'Nucleoside Analog Delayed Chain Terminator',
    referenceSmiles: 'CCC(CC)COC(=O)C(C)NP(=O)(OCC1OC(C#N)(c2ccc3n2ncnc3N)C(O)C1O)Oc4ccccc4',
    affinity: {
      kd_nm: 55.0,
      ic50_nm: 770.0,
      delta_g_kcal_mol: -9.9,
      bindingClass: 'Active Nucleotide Inhibitor'
    },
    admet: {
      mw_da: 602.59,
      logp: 2.31,
      tpsa_a2: 203.55,
      hbd: 4,
      hba: 12,
      rotatableBonds: 13,
      caco2Permeability: 'Low (IV formulation)',
      clearanceRisk: 'Esterase / Phosphoramidase',
      bloodBrainBarrier: 'Low'
    },
    epistemicTag: 'Illustrative'
  },
  {
    id: '4TZK',
    pdbId: '4TZK',
    name: 'M. tuberculosis InhA (Enoyl-ACP Reductase)',
    gene: 'InhA',
    mutation: 'Wild-Type',
    category: 'Infectious Disease',
    resolutionA: 1.62,
    ligandName: 'Pyrrolidine Carboxamide',
    ligandCcd: '33F',
    pocketName: 'NADH-Binding / Substrate Fatty Acyl Subpocket',
    pocketResidues: ['Gly96', 'Phe149', 'Tyr158', 'Met161', 'Met199', 'Leu207', 'Ile215'],
    modality: 'Direct Non-Covalent InhA Inhibitor (Bypasses KatG Activation)',
    referenceSmiles: 'Cc1cc(F)cc(c1)NC(=O)C2CCCN2C(=O)c3ccc(o3)c4ccccc4',
    affinity: {
      kd_nm: 1.8,
      ic50_nm: 8.0,
      delta_g_kcal_mol: -11.9,
      bindingClass: 'Direct Catalytic Inhibitor'
    },
    admet: {
      mw_da: 392.43,
      logp: 4.64,
      tpsa_a2: 62.55,
      hbd: 1,
      hba: 3,
      rotatableBonds: 4,
      caco2Permeability: 'High',
      clearanceRisk: 'Low',
      bloodBrainBarrier: 'Moderate'
    },
    epistemicTag: 'Illustrative'
  }
];

// Category index mappings
const CATEGORIES = [
  'Repo Benchmark Core',
  'Oncology Kinases',
  'Cell Cycle & PPI',
  'Infectious Disease'
];

// Map lookup tables
const BY_ID = Object.freeze(
  TARGET_PRESETS_DATA.reduce((acc, t) => {
    acc[t.pdbId.toUpperCase()] = Object.freeze(t);
    return acc;
  }, {})
);

const BY_CATEGORY = Object.freeze(
  CATEGORIES.reduce((acc, cat) => {
    acc[cat] = Object.freeze(TARGET_PRESETS_DATA.filter((t) => t.category === cat));
    return acc;
  }, {})
);

/**
 * Public TARGET_PRESETS API Object
 */
export const TARGET_PRESETS = Object.freeze({
  categories: Object.freeze([...CATEGORIES]),
  all: Object.freeze([...TARGET_PRESETS_DATA]),
  byCategory: BY_CATEGORY,
  byId: BY_ID,

  /**
   * Return array of all 16 PDB identifiers
   * @returns {string[]}
   */
  getPdbIds() {
    return TARGET_PRESETS_DATA.map((t) => t.pdbId);
  },

  /**
   * Retrieve target metadata object by PDB code
   * @param {string} pdbId 4-character PDB code (e.g. '7RPZ')
   * @returns {Object|null}
   */
  getTarget(pdbId) {
    if (!pdbId || typeof pdbId !== 'string') return null;
    return BY_ID[pdbId.trim().toUpperCase()] || null;
  },

  /**
   * Retrieve targets belonging to a specific therapeutic category
   * @param {string} category 
   * @returns {Object[]}
   */
  getByCategory(category) {
    return BY_CATEGORY[category] || [];
  }
});

// UMD / Global window attachment for non-ESM browser contexts
if (typeof window !== 'undefined') {
  window.TARGET_PRESETS = TARGET_PRESETS;
}
if (typeof globalThis !== 'undefined') {
  globalThis.TARGET_PRESETS = TARGET_PRESETS;
}
