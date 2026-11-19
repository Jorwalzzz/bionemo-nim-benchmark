/**
 * Central reactive state, configurations, and chemical/biological constants
 * for the Agentic BioNeMo Discovery Cockpit.
 */

// Host Sentinel (detects GitHub Pages / Cloudflare Pages / Static vs Local Workstation server)
export const isStaticHost = window.location.protocol === 'file:' || 
                     window.location.hostname.endsWith('github.io') || 
                     window.location.hostname.endsWith('pages.dev') ||
                     (window.location.protocol.startsWith('http') && window.location.port !== '8000');

export const isLocalServer = window.location.protocol.startsWith('http') && 
                      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
                      window.location.port === '8000';

// ESMFold De Novo Presets
export const ESMFOLD_PRESETS = {
  kras: {
    name: 'KRAS G12D Oncogenic Variant',
    seq: 'MTEYKLVVVGAGDVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDLPSRTVDTKQAQDLARSYGIPFIETSAKTRQRVEDAFYTLVREIRQYRLKKISKEEKTPGCVKIKKCIIM'
  },
  braf: {
    name: 'BRAF V600E Kinase Domain',
    seq: 'FGLATVKSRWSGSHQFEQLSGSILWMAPEVIRMQDKNPYSFQSDVYAFGIVLYELMTGQLPYSNINNRDQIIFMVGRGYLSPDLSKVRSNCPKAMKRLMAECLKKKRDERPLFPQILASIELLARSLPKIHRSASEPSLNRAGFQTEDFSLYACASPKTPIQAGGYGAFPVH'
  },
  mpro: {
    name: 'SARS-CoV-2 Mpro C145A Protease',
    seq: 'SGFRKMAFPSGKVEGCMVQVTCGTTTLNGLWLDDVVYCPRHVICTSEDMLNPNYEDLLIRKSNHNFLVQAGNVQLRVIGHSMQNCVLKLKVDTANPKTPKYKFVRIQPGQTFSVLACYNGSPSGVYQCAMRPNFTIKGSFLNGSCGSVGFNIDYDCVSFCYMHHMELPTGVHAGTDLEGNFYGPFVDRQTAQAAGTDTTITVNVLAWLYAAVINGDRWFLNRFTTTLNDFNLVAMKYNYEPLTQDHVDILGPLSAQTGIAVLDMCAASLGS'
  }
};

// Small Molecule Preset Inhibitors
export const PRESET_INHIBITORS = {
  kras: { name: 'MRTX1133 (KRAS G12D)', smiles: 'C#CC1=C(C=CC2=CC(=CC(=C21)C3=NC=C4C(=C3F)N=C(N=C4N5CC6CCC(C5)N6)OCC78CCCN7CC(C8)F)O)F' },
  egfr: { name: 'Osimertinib (EGFR T790M)', smiles: 'CN1C=C(C2=CC=CC=C21)C3=NC(=NC=C3)NC4=C(C=C(C(=C4)NC(=O)C=C)N(C)CCN(C)C)OC' },
  mpro: { name: 'Nirmatrelvir (Paxlovid)', smiles: 'CC1(C2C1C(N(C2)C(=O)C(C(C)(C)C)NC(=O)C(F)(F)F)C(=O)NC(CC3CCNC3=O)C#N)C' },
  her2: { name: 'Tucatinib (HER2 Kinase)', smiles: 'CC1=C(C=CC(=C1)NC2=NC=NC3=C2C=C(C=C3)NC4=NC(CO4)(C)C)OC5=CC6=NC=NN6C=C5' }
};

// Verified Crystallographic Targets
export const TARGETS = {
  'KRAS G12D': { pdb: '8AZV', indication: 'Colorectal/NSCLC', pocket: 'Switch II', mutant: 'G12D', color: '#76b900' },
  'EGFR T790M': { pdb: '2ITZ', indication: 'NSCLC', pocket: 'ATP Binding', mutant: 'T790M', color: '#00f1fd' },
  'SARS-CoV-2 Mpro': { pdb: '7BQY', indication: 'COVID-19', pocket: 'Cys145 Dyad', mutant: '—', color: '#f59e0b' },
  'HER2': { pdb: '3PP0', indication: 'Breast/Gastric', pocket: 'Kinase Domain', mutant: 'Amplified', color: '#a855f7' },
};

// Empirical Benchmark Leads Database
export const EMPIRICAL_TARGET_LEADS = {
  "KRAS G12D": [
    {
      "id": "MRTX1133-NIM-01",
      "name": "MRTX1133 G12D Specific Inhibitor",
      "smiles": "O=C(N1CCN(C2=NC=C(F)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5",
      "affinity": -10.45,
      "qed": 0.309,
      "mw": 531.51,
      "logp": 5.55,
      "sascore": 6.46,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Asp12, Tyr96, Gln61, Gly10"
    },
    {
      "id": "BI-2865-NIM-02",
      "name": "BI-2865 Pan-KRAS Switch-II Binder",
      "smiles": "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)C4=NC5=C(N4)C=CC(=C5)F",
      "affinity": -9.85,
      "qed": 0.457,
      "mw": 457.55,
      "logp": 4.68,
      "sascore": 5.94,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Asp12, Glu62, Tyr96"
    },
    {
      "id": "KRAS-PYR-03",
      "name": "Asp12-Targeting Pyrido-Pyrimidine",
      "smiles": "FC1=CC=C(C2=C(Cl)C=CC=C2)C3=C1N=CN=C3NC4=CC=C(N5CCN(C)CC5)C=C4",
      "affinity": -9.4,
      "qed": 0.442,
      "mw": 447.95,
      "logp": 5.58,
      "sascore": 5.87,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Asp12, Lys16, Tyr96"
    },
    {
      "id": "SOTO-ISO-04",
      "name": "Sotorasib Bioisostere Analogue",
      "smiles": "CC(C)N1CCN(CC1)C(=O)C2=NC(=NC3=CC(=C(C=C32)F)Cl)NC4=C(C)C=CC=C4C",
      "affinity": -8.95,
      "qed": 0.603,
      "mw": 455.97,
      "logp": 4.95,
      "sascore": 5.52,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Tyr96, Met72, Val9"
    },
    {
      "id": "SW2-MIM-05",
      "name": "Switch-II Sulfo-Indazole Mimetic",
      "smiles": "O=C(Nc1ccc(cc1)S(=O)(=O)N)c2cnc3[nH]c(nc3c2)c4ccc(F)cc4",
      "affinity": -8.7,
      "qed": 0.475,
      "mw": 411.42,
      "logp": 2.66,
      "sascore": 4.42,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Gln61, Glu62, Arg68"
    },
    {
      "id": "FLAG-IND-06",
      "name": "Pyrazino-Indole Lead (Metabolic Risk)",
      "smiles": "CN1CCN(CC1)c2nc3cc(ccc3o2)C(=O)Nc4ccc(F)c(Cl)c4",
      "affinity": -8.35,
      "qed": 0.742,
      "mw": 388.83,
      "logp": 3.62,
      "sascore": 4.34,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Ala59, Gly60"
    },
    {
      "id": "MACRO-FLAG-07",
      "name": "Macrocyclic Peptide (Ro5 Alert)",
      "smiles": "CC(C)CC(C(=O)NC(C)C(=O)NC(CC1=CC=C(O)C=C1)C(=O)N2CCCC2C(=O)N)NC(=O)C",
      "affinity": -8.1,
      "qed": 0.283,
      "mw": 503.6,
      "logp": -0.05,
      "sascore": 6.76,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Lys16, Ser17"
    },
    {
      "id": "PHEN-FLAG-08",
      "name": "Dihydrophenanthridine (High cLogP)",
      "smiles": "Clc1ccc(cc1)n2c(=O)c3ccccc3c4ccccc24",
      "affinity": -7.8,
      "qed": 0.463,
      "mw": 305.76,
      "logp": 4.8,
      "sascore": 5.17,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Val9, Leu56"
    }
  ],
  "EGFR T790M": [
    {
      "id": "OSIMERTINIB-NIM",
      "name": "Osimertinib (AZD9291) 3rd-Gen Mutant Selective",
      "smiles": "CN(C)CC=CC(=O)Nc1cc(Nc2nccc(n2)c3cn(C)c4ccccc34)c(cc1OC)N(C)CCN(C)C",
      "affinity": -10.8,
      "qed": 0.248,
      "mw": 556.72,
      "logp": 4.44,
      "sascore": 5.83,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Met790, Cys797, Lys745"
    },
    {
      "id": "ROCILET-NIM-02",
      "name": "Rociletinib Pyrimidine Derivative",
      "smiles": "CC(=O)N1CCN(CC1)C2=CC=C(NC3=NC=C(C4=CN(C5=CC=CC=C45)C)C(=N3)NC6=CC=CC(=C6)C(F)(F)F)C=C2",
      "affinity": -10.15,
      "qed": 0.228,
      "mw": 585.63,
      "logp": 6.81,
      "sascore": 6.6,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Met790, Thr854, Leu844"
    },
    {
      "id": "LAZER-NIM-03",
      "name": "Lazertinib Bioisosteric Scaffold",
      "smiles": "CN1CCN(CC1)c2cc(NC(=O)C=C)c(OC)cc2Nc3ncc(Cl)c(n3)c4cn(C)c5ccccc45",
      "affinity": -9.85,
      "qed": 0.327,
      "mw": 532.05,
      "logp": 4.92,
      "sascore": 6.08,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Met790, Cys797, Glu762"
    },
    {
      "id": "GEFIT-ANALOG-04",
      "name": "Gefitinib Reversible Analogue",
      "smiles": "COC1=C(OCCCN2CCOCC2)C=C3C(=C1)N=CN=C3NC4=CC(=C(C=C4)F)Cl",
      "affinity": -9.2,
      "qed": 0.518,
      "mw": 446.91,
      "logp": 4.28,
      "sascore": 4.49,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Lys745, Thr790, Phe723"
    },
    {
      "id": "PYRAZO-NIM-05",
      "name": "Pyrazolopyrimidine Kinase Scaffold",
      "smiles": "CC1=CN=C(C=C1)NC2=NC=C(F)C(=N2)NC3=CC=C(N4CCN(C)CC4)C=C3",
      "affinity": -8.9,
      "qed": 0.687,
      "mw": 393.47,
      "logp": 3.56,
      "sascore": 4.42,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Met793, Leu718"
    },
    {
      "id": "ERLOT-SCAF-06",
      "name": "Erlotinib Ethynyl Core",
      "smiles": "COC1=C(OC)C=C2C(=C1)N=CN=C2NC3=CC=CC(=C3)C#C",
      "affinity": -8.65,
      "qed": 0.749,
      "mw": 305.34,
      "logp": 3.37,
      "sascore": 3.85,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Gln791, Met793"
    },
    {
      "id": "QUIN-FLAG-07",
      "name": "Tri-Chloro Quinazoline (Lipophilicity Alert)",
      "smiles": "Clc1cc2c(Nc3ccc(Cl)c(Cl)c3)ncnc2cc1OCC4CCCCC4",
      "affinity": -8.2,
      "qed": 0.456,
      "mw": 436.77,
      "logp": 7.29,
      "sascore": 5.38,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Leu844, Val726"
    },
    {
      "id": "DIMER-FLAG-08",
      "name": "Dianilinopyrimidine Dimer",
      "smiles": "c1ccc(cc1)Nc2nccc(n2)Nc3ccccc3",
      "affinity": -7.6,
      "qed": 0.747,
      "mw": 262.32,
      "logp": 3.96,
      "sascore": 3.75,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Thr854, Lys745"
    }
  ],
  "SARS-CoV-2 Mpro": [
    {
      "id": "NIRMATRELVIR-NIM",
      "name": "Nirmatrelvir (PF-07321332) Covalent Mpro Inhibitor",
      "smiles": "CC1(C2C1C(N(C2)C(=O)C(C(C)(C)C)NC(=O)C(F)(F)F)C(=O)NC(CC3CCNC3=O)C#N)C",
      "affinity": -11.2,
      "qed": 0.504,
      "mw": 499.53,
      "logp": 1.1,
      "sascore": 6.97,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Cys145, His41, Glu166, Gln189"
    },
    {
      "id": "ENSITRELVIR-NIM",
      "name": "Ensitrelvir (S-217622) Non-Covalent Triazine",
      "smiles": "CC1=NC(=C(N1CC2=C(C=CC(=C2F)F)F)C3=CC(=C(C=C3)C#N)F)NC(=O)C4=CC(=NN4C)C(F)(F)F",
      "affinity": -10.65,
      "qed": 0.276,
      "mw": 536.41,
      "logp": 5.34,
      "sascore": 5.73,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "His41, Cys145, Met165, Glu166"
    },
    {
      "id": "GC376-ANALOG-03",
      "name": "GC-376 Dipeptide Nitrile Surrogate",
      "smiles": "CC(C)CC(NC(=O)OCC1=CC=CC=C1)C(=O)NC(CC2CCNC2=O)C(=O)C#N",
      "affinity": -10.1,
      "qed": 0.482,
      "mw": 428.49,
      "logp": 1.43,
      "sascore": 5.14,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Cys145, His163, Phe140"
    },
    {
      "id": "BOCEP-NIM-04",
      "name": "Boceprevir Ketoamide Derivative",
      "smiles": "CC1(C2C1C(N(C2)C(=O)C(NC(=O)NC(C)(C)C)C(C)(C)C)C(=O)NC(CC3CCCCC3)C(=O)C(=O)N)C",
      "affinity": -9.55,
      "qed": 0.344,
      "mw": 547.74,
      "logp": 2.49,
      "sascore": 7.67,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "His41, Gly143, Glu166"
    },
    {
      "id": "BENZOTH-NIM-05",
      "name": "Chlorobenzoyl Benzothiazole Peptidomimetic",
      "smiles": "CC(C)CC(NC(=O)C1=CC=C(Cl)C=C1)C(=O)NC2=NC3=CC=CC=C3S2",
      "affinity": -9.1,
      "qed": 0.627,
      "mw": 401.92,
      "logp": 4.73,
      "sascore": 5.45,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Met49, Cys145, Met165"
    },
    {
      "id": "OXADIAZ-NIM-06",
      "name": "Oxadiazole Covalent Warhead",
      "smiles": "O=C(NC1CC1)C2=NN=C(O2)c3ccc(cc3)NC(=O)c4ccccc4",
      "affinity": -8.8,
      "qed": 0.739,
      "mw": 348.36,
      "logp": 2.88,
      "sascore": 4.31,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Asn142, Gly143, Cys145"
    },
    {
      "id": "PEPT-FLAG-07",
      "name": "Extended Tetrapeptide (Metabolic Liability)",
      "smiles": "CC(C)CC(NC(=O)C(CC1=CC=CC=C1)NC(=O)C(CCC(=O)O)NC(=O)C)C(=O)NC(CC2CCNC2=O)C=O",
      "affinity": -8.3,
      "qed": 0.135,
      "mw": 587.67,
      "logp": -0.18,
      "sascore": 7.42,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Glu166, Pro168"
    },
    {
      "id": "TRAP-FLAG-08",
      "name": "Trifluoromethyl Aniline \u03b1-Diketone",
      "smiles": "FC(F)(F)c1ccc(cc1)C(=O)NC(Cc2ccccc2)C(=O)NC(CC3CCNC3=O)C(=O)C(=O)Nc4ccc(F)cc4",
      "affinity": -8.05,
      "qed": 0.195,
      "mw": 612.58,
      "logp": 3.4,
      "sascore": 7.29,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "His41, Tyr54"
    }
  ],
  "HER2": [
    {
      "id": "TUCATINIB-NIM",
      "name": "Tucatinib (ONT-380) Kinase Selective",
      "smiles": "CC1=NN2C(=NN=C2C3=CC=C(C=C3)OC4=CC=C5C(=C4)N=CN=C5NC6=CC(=C(C=C6)F)Cl)C=C1",
      "affinity": -10.9,
      "qed": 0.296,
      "mw": 497.92,
      "logp": 6.37,
      "sascore": 6.36,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Met801, Thr798, Lys753, Leu852"
    },
    {
      "id": "NERAT-NIM-02",
      "name": "Neratinib Irreversible Covalent Analogue",
      "smiles": "CCOC1=C(C=C2C(=C1)N=CN=C2NC3=CC(=C(C=C3)OCC4=NC=CC=C4)Cl)NC(=O)C=CC(C)(C)N(C)C",
      "affinity": -10.35,
      "qed": 0.208,
      "mw": 561.09,
      "logp": 6.23,
      "sascore": 5.8,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Cys805, Met801, Leu726"
    },
    {
      "id": "AFATINIB-NIM-03",
      "name": "Afatinib Pyrrolidino Derivative",
      "smiles": "CN(C)CC=CC(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC4CCOC4",
      "affinity": -9.95,
      "qed": 0.457,
      "mw": 485.95,
      "logp": 4.39,
      "sascore": 5.04,
      "pareto": true,
      "verdict": "PASS",
      "contacts": "Cys805, Lys753, Asp863"
    },
    {
      "id": "LAPAT-NIM-04",
      "name": "Lapatinib Fluorobenzyl Core",
      "smiles": "CS(=O)(=O)CCNCC1=CC=C(O1)C2=CC=C3C(=C2)N=CN=C3NC4=CC(=C(C=C4)OCC5=CC(=CC=C5)F)Cl",
      "affinity": -9.4,
      "qed": 0.179,
      "mw": 581.07,
      "logp": 6.14,
      "sascore": 6.15,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Met801, Thr862, Phe731"
    },
    {
      "id": "PYRROLO-NIM-05",
      "name": "Pyrrolopyrimidine Reversible Scaffold",
      "smiles": "CN1C=C(C2=CC=CC=C21)C3=NC(=NC=C3)NC4=CC=C(C=C4)N5CCOCC5",
      "affinity": -9.0,
      "qed": 0.57,
      "mw": 385.47,
      "logp": 4.22,
      "sascore": 4.77,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Leu796, Met801"
    },
    {
      "id": "ISOFLAV-NIM-06",
      "name": "Isoflavone Hydroxylated ATP Blocker",
      "smiles": "OC1=CC=C(C=C1)C2=COC3=C(C2=O)C=C(O)C(=C3)C4=CC=CC=C4",
      "affinity": -8.6,
      "qed": 0.566,
      "mw": 330.34,
      "logp": 4.54,
      "sascore": 5.28,
      "pareto": false,
      "verdict": "PASS",
      "contacts": "Val734, Ala751"
    },
    {
      "id": "BISARYL-FLAG-07",
      "name": "Bis-Aryl Quinazoline Dimer (MW > 800)",
      "smiles": "Clc1ccc(Nc2ncnc3cc(OCCCN4CCN(CCOc5ccc(Nc6ncnc7cc(OCCCN8CCOCC8)c(OC)cc67)cc5)CC4)c(OC)cc23)cc1F",
      "affinity": -8.15,
      "qed": 0.073,
      "mw": 882.44,
      "logp": 7.44,
      "sascore": 8.0,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Lys753, Asp863"
    },
    {
      "id": "POLYAROM-FLAG-08",
      "name": "Insoluble Polyaromatic Hydrocarbon",
      "smiles": "c1ccc2c(c1)c3cccc4c3c2cc5c4cccc5",
      "affinity": -7.7,
      "qed": 0.313,
      "mw": 252.32,
      "logp": 5.64,
      "sascore": 5.45,
      "pareto": false,
      "verdict": "FLAGGED",
      "contacts": "Val734, Leu852"
    }
  ]
};

// Central Reactive Cockpit State
export const state = {
  selectedRounds: 2,
  currentCustomPdb: null,
  currentSelectedLead: null,
  currentTargetTab: 'presets',
  currentTargetSeq: '',
  currentTargetPdbText: null,
  currentTargetPocketResidues: ['GLY12', 'ASP12', 'GLN61', 'TYR96'],
  currentTargetIsEsmfold: false,
  currentTargetMeanPlddt: 90.0,
  currentLeads: [],
  isRunning: false,
  currentOt2Code: '',
  currentLabCardMd: '',
  latestResistanceData: null,
  currentTourStep: 0,
  trialState: {
    runsRemaining: 10,
    runsTotal: 10,
    tier: 'Enterprise Trial',
    lastResetDate: null
  },
  CLIENT_FP: null
};

if (typeof window !== 'undefined') {
  window.state = state;
  const reactiveProps = [
    'selectedRounds',
    'currentCustomPdb',
    'currentSelectedLead',
    'currentTargetTab',
    'currentTargetSeq',
    'currentTargetPdbText',
    'currentTargetPocketResidues',
    'currentTargetIsEsmfold',
    'currentTargetMeanPlddt',
    'currentLeads',
    'isRunning',
    'currentOt2Code',
    'currentLabCardMd',
    'latestResistanceData',
    'currentTourStep',
    'CLIENT_FP'
  ];

  reactiveProps.forEach(prop => {
    Object.defineProperty(window, prop, {
      get: () => state[prop],
      set: (v) => { state[prop] = v; },
      configurable: true
    });
  });
}
