/**
 * BioNeMo NIM Inference Benchmark - Interactive Lead Series & R-Group Discovery Studio
 * Module: ./js/studio.js
 */

const BASE_SERIES = {
  lead_01: {
    id: 'NIM-LEAD-01-CORE',
    name: 'Lead 01 Core (MRTX1133)',
    smiles: 'CN1CCN(CC1)C2=NC=C(Cl)C3=C2C(=CC=C3)C4=C(F)C=CC=C4F',
    deltaG: -4.80,
    mmgbsa: -10.45,
    qed: 0.420,
    sascore: 4.85,
    mw: 378.50,
    clogp: 3.85,
    ro5Violations: 0,
    activeVector: 'Asp12, Gln61, Tyr96',
    reconciledNote: 'MRTX1133 Core Fragment (378.5 Da vs 600.64 Da Full Clinical)'
  },
  lead_02: {
    id: 'NIM-LEAD-01-03',
    name: 'Lead 02 +F (Nominated)',
    smiles: 'O=C(N1CCN(C2=NC=C(F)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5',
    deltaG: -4.81,
    mmgbsa: -10.82,
    qed: 0.309,
    sascore: 7.74,
    mw: 531.51,
    clogp: 5.55,
    ro5Violations: 2,
    activeVector: 'Asp12, Tyr96, Gln61',
    reconciledNote: 'Multi-Objective Pareto Optimal Screening Hit'
  },
  lead_03: {
    id: 'NIM-LEAD-01-EVO',
    name: 'Lead 03 Evolved (Bioisostere)',
    smiles: 'O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5',
    deltaG: -4.92,
    mmgbsa: -11.15,
    qed: 0.335,
    sascore: 7.20,
    mw: 547.97,
    clogp: 5.80,
    ro5Violations: 2,
    activeVector: 'Asp12 Salt Bridge + Gln61 H-Bond',
    reconciledNote: 'Evolved Bioisosteric Scaffold'
  }
};

const TARGET_OVERRIDES = {
  '8AZV': null,
  '4MNE': {
    id: 'BRAF-V600E-CORE',
    name: 'BRAF V600E // Kinase Domain',
    smiles: 'CC(C)(C)C1=NC(=C(S1)C2=NC(=NC=C2)N)C3=C(F)C(NS(=O)(=O)C4=C(F)C=CC=C4F)=CC=C3',
    deltaG: -4.65,
    mmgbsa: -9.80,
    qed: 0.412,
    sascore: 5.40,
    mw: 519.56,
    clogp: 4.92,
    ro5Violations: 1,
    activeVector: 'Glu501, Phe595, Glu600',
    reconciledNote: '4MNE BRAF V600E Reference Analog (519.6 Da)'
  },
  '7BQY': {
    id: 'MPRO-CAT-CORE',
    name: 'SARS-CoV-2 Mpro // Catalytic Dyad',
    smiles: 'CC(=O)NC(C1=CC=CC=C1)C(=O)NC(CC(=O)OC)C(=O)NC2CCC(=O)NC2=O',
    deltaG: -5.12,
    mmgbsa: -11.20,
    qed: 0.284,
    sascore: 6.15,
    mw: 680.80,
    clogp: 2.65,
    ro5Violations: 1,
    activeVector: 'His41, Cys145, His163',
    reconciledNote: '7BQY Mpro Peptidomimetic Inhibitor Core'
  }
};

let currentTargetId = '8AZV';
let currentSeriesKey = 'lead_02';
const activeModifiers = new Set();
const activeAnimations = new WeakMap();

let seriesPillBtns = [];
let modifierChipBtns = [];
let smilesDisplayEl = null;
let metricDeltaGEl = null;
let metricMmgbsaEl = null;
let metricQedEl = null;
let metricSascoreEl = null;
let metricMwEl = null;
let metricClogpEl = null;
let metricRo5El = null;
let metricVectorEl = null;
let scaffoldNoteEl = null;

function animateValue(element, start, end, durationMs, decimals, suffix = '') {
  if (!element) return;
  const prevRaf = activeAnimations.get(element);
  if (prevRaf) cancelAnimationFrame(prevRaf);

  const safeStart = Number.isFinite(start) ? start : end;
  const startTime = performance.now();
  const diff = end - safeStart;

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(1, elapsed / durationMs);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = safeStart + diff * eased;
    element.textContent = `${current.toFixed(decimals)}${suffix}`;

    if (progress < 1) {
      activeAnimations.set(element, requestAnimationFrame(step));
    } else {
      element.textContent = `${end.toFixed(decimals)}${suffix}`;
      activeAnimations.delete(element);
    }
  }

  activeAnimations.set(element, requestAnimationFrame(step));
}

function getBaseSeries() {
  if (currentTargetId !== '8AZV' && TARGET_OVERRIDES[currentTargetId]) {
    const override = TARGET_OVERRIDES[currentTargetId];
    if (currentSeriesKey === 'lead_01') {
      return { ...override, deltaG: override.deltaG + 0.15, mw: Math.max(320, override.mw - 42), ro5Violations: 0 };
    }
    if (currentSeriesKey === 'lead_03') {
      return { ...override, deltaG: override.deltaG - 0.18, mmgbsa: override.mmgbsa - 0.45, qed: Math.min(0.85, override.qed + 0.03) };
    }
    return override;
  }
  return BASE_SERIES[currentSeriesKey] || BASE_SERIES.lead_02;
}

function appendSmilesSubstituent(smiles, modTag) {
  if (modTag === 'f') {
    if (smiles.includes('C2=NC=C(')) return smiles.replace('C2=NC=C(', 'C2=NC(F)=C(');
    return smiles.replace(/C1=CC=CC=C1/, 'C1=C(F)C=CC=C1');
  }
  if (modTag === 'cf3') {
    return `${smiles.replace(/F$/, '')}(C(F)(F)F)`;
  }
  if (modTag === 'me') {
    return smiles.replace(/C(=O)/, 'C(=O)C');
  }
  if (modTag === 'pyridine') {
    return smiles.replace(/C1=CC=CC=C1/, 'C1=NC=CC=C1').replace(/C3=C2/, 'N3=C2');
  }
  return smiles;
}

function updateDiscoveryMetrics() {
  const base = getBaseSeries();

  let dG = base.deltaG;
  let mmgbsa = base.mmgbsa;
  let mw = base.mw;
  let clogp = base.clogp;
  let qed = base.qed;
  let sascore = base.sascore;
  let smiles = base.smiles;
  let ro5 = base.ro5Violations;

  if (activeModifiers.has('f')) {
    dG -= 0.18;
    mmgbsa -= 0.35;
    mw += 18.0;
    clogp += 0.22;
    smiles = appendSmilesSubstituent(smiles, 'f');
  }
  if (activeModifiers.has('cf3')) {
    dG -= 0.32;
    mmgbsa -= 0.55;
    mw += 68.0;
    clogp += 0.88;
    qed = Math.max(0.1, qed - 0.04);
    sascore += 0.3;
    smiles = appendSmilesSubstituent(smiles, 'cf3');
  }
  if (activeModifiers.has('me')) {
    dG += 0.05;
    mmgbsa -= 0.12;
    mw += 14.0;
    clogp += 0.45;
    smiles = appendSmilesSubstituent(smiles, 'me');
  }
  if (activeModifiers.has('pyridine')) {
    dG -= 0.12;
    mmgbsa -= 0.28;
    clogp -= 0.35;
    qed = Math.min(0.85, qed + 0.03);
    smiles = appendSmilesSubstituent(smiles, 'pyridine');
  }

  // Recompute Lipinski violation count coherently from modified MW & cLogP
  ro5 = (mw > 500 ? 1 : 0) + (clogp > 5 ? 1 : 0);

  if (smilesDisplayEl) smilesDisplayEl.textContent = smiles;
  if (metricVectorEl) metricVectorEl.textContent = base.activeVector;
  if (scaffoldNoteEl) scaffoldNoteEl.textContent = base.reconciledNote;

  if (metricDeltaGEl) {
    animateValue(metricDeltaGEl, parseFloat(metricDeltaGEl.textContent), dG, 300, 2, ' kcal/mol');
  }
  if (metricMmgbsaEl) {
    animateValue(metricMmgbsaEl, parseFloat(metricMmgbsaEl.textContent), mmgbsa, 300, 2, ' kcal/mol');
  }
  if (metricMwEl) {
    animateValue(metricMwEl, parseFloat(metricMwEl.textContent), mw, 300, 1, ' Da');
  }
  if (metricClogpEl) {
    animateValue(metricClogpEl, parseFloat(metricClogpEl.textContent), clogp, 300, 2);
  }
  if (metricQedEl) {
    animateValue(metricQedEl, parseFloat(metricQedEl.textContent), qed, 300, 3);
  }
  if (metricSascoreEl) {
    animateValue(metricSascoreEl, parseFloat(metricSascoreEl.textContent), sascore, 300, 2);
  }
  if (metricRo5El) {
    metricRo5El.textContent = ro5 === 0 ? '0 Violations (Pass)' : `${ro5} Violation${ro5 > 1 ? 's' : ''}`;
    metricRo5El.style.color = ro5 === 0 ? 'var(--color-signal-green)' : '#F59E0B';
  }
}

export function setSeries(key) {
  if (!BASE_SERIES[key]) return;
  currentSeriesKey = key;
  seriesPillBtns.forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-series') === key);
  });
  updateDiscoveryMetrics();
}

export function toggleModifier(modKey) {
  if (activeModifiers.has(modKey)) {
    activeModifiers.delete(modKey);
  } else {
    activeModifiers.add(modKey);
  }
  modifierChipBtns.forEach(btn => {
    const k = btn.getAttribute('data-mod');
    btn.classList.toggle('active', activeModifiers.has(k));
  });
  updateDiscoveryMetrics();
}

function init() {
  seriesPillBtns = Array.from(document.querySelectorAll('.lead-series-pill'));
  modifierChipBtns = Array.from(document.querySelectorAll('.lead-mod-chip'));
  smilesDisplayEl = document.getElementById('hud-smiles-display');
  metricDeltaGEl = document.getElementById('hud-metric-deltag');
  metricMmgbsaEl = document.getElementById('hud-metric-mmgbsa');
  metricQedEl = document.getElementById('hud-metric-qed');
  metricSascoreEl = document.getElementById('hud-metric-sascore');
  metricMwEl = document.getElementById('hud-metric-mw');
  metricClogpEl = document.getElementById('hud-metric-clogp');
  metricRo5El = document.getElementById('hud-metric-ro5');
  metricVectorEl = document.getElementById('hud-metric-vector');
  scaffoldNoteEl = document.getElementById('hud-scaffold-note');

  seriesPillBtns.forEach(btn => {
    btn.addEventListener('click', () => setSeries(btn.getAttribute('data-series')));
  });
  modifierChipBtns.forEach(btn => {
    btn.addEventListener('click', () => toggleModifier(btn.getAttribute('data-mod')));
  });

  setSeries('lead_02');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

window.addEventListener('bionemo:target-changed', (e) => {
  const target = e.detail;
  if (!target) return;
  currentTargetId = target.id || '8AZV';
  updateDiscoveryMetrics();
  if (metricVectorEl && Array.isArray(target.pocketResidueNames)) {
    metricVectorEl.textContent = target.pocketResidueNames.join(', ');
  }
});

window.BioNeMoStudio = {
  setSeries,
  toggleModifier,
  getSeriesData: () => getBaseSeries()
};
