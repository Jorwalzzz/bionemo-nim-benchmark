/**
 * BioNeMo NIM Inference Benchmark - Cinematic 3D Molecular Pose Lab
 * Module: ./js/molviewer.js
 *
 * Implements:
 * 1. 3Dmol.js near-full-bleed WebGL viewport with centered receptor-ligand framing.
 * 2. Multi-target switcher (KRAS G12D 8AZV, BRAF V600E 4MNE, SARS-CoV-2 Mpro 7BQY).
 * 3. Request cancellation (AbortController + monotonic sequence token) + finite CDN retry limit.
 * 4. Computed protein-ligand polar contacts (2.2 <= d <= 3.5 A) from parsed PDB coordinates (zero fake offsets).
 */

import { escapeHtml } from './shared/dom-utils.js';

const TARGET_REGISTRY = {
  '8AZV': {
    id: '8AZV',
    name: 'KRAS G12D // Switch-II Pocket',
    gene: 'KRAS',
    uniprot: 'P01116',
    mutant: 'G12D',
    pocketResidues: [12, 61, 96],
    pocketResidueNames: ['Asp12', 'Gln61', 'Tyr96'],
    indication: 'Pancreatic / Colorectal Adenocarcinoma',
    ligandResns: ['6IC'],
    ligandName: 'MRTX1133 Core Fragment',
    ligandMW: '378.5 Da (600.64 Da Full Clinical)',
    bindingDeltaG: '-10.45 kcal/mol (MM-GBSA)'
  },
  '4MNE': {
    id: '4MNE',
    name: 'BRAF V600E // Kinase Domain',
    gene: 'BRAF',
    uniprot: 'P15056',
    mutant: 'V600E',
    pocketResidues: [501, 595, 600],
    pocketResidueNames: ['Glu501', 'Phe595', 'Glu600'],
    indication: 'Metastatic Melanoma / Thyroid Carcinoma',
    ligandResns: ['573'],
    ligandName: 'Dabrafenib Core Bioisostere',
    ligandMW: '519.56 Da',
    bindingDeltaG: '-9.80 kcal/mol (MM-GBSA)'
  },
  '7BQY': {
    id: '7BQY',
    name: 'SARS-CoV-2 Mpro // Catalytic Dyad',
    gene: 'Mpro / 3CLpro',
    uniprot: 'P0DTD1',
    mutant: 'Wild-Type',
    pocketResidues: [41, 145, 163],
    pocketResidueNames: ['His41', 'Cys145', 'His163'],
    indication: 'Viral Protease Inhibition',
    ligandResns: ['010', '02J', 'PJE'],
    ligandName: 'N3 Bioisosteric Inhibitor',
    ligandMW: '680.8 Da',
    bindingDeltaG: '-11.20 kcal/mol (MM-GBSA)'
  }
};

const EXCLUDED_HETERO = new Set([
  'HOH', 'WAT', 'DOD', 'MG', 'ZN', 'CA', 'CL', 'NA', 'K', 'MN', 'FE', 'BR', 'IOD',
  'SO4', 'PO4', 'GOL', 'EDO', 'PEG', 'DMS', 'ACT', 'GDP', 'GTP', 'ATP', 'ADP', 'ACP', 'ANP'
]);

let viewer = null;
let currentTargetId = '8AZV';
let isRotating = false;
let isSurfaceActive = false;
let surfaceObj = null;
let requestSeq = 0;
let activeFetchController = null;
let cdnRetryCount = 0;
const MAX_CDN_RETRIES = 25;

let containerEl = null;
let scanOverlayEl = null;
let statusBadgeEl = null;
let targetPillBtns = [];
let btnRotate = null;
let btnFocus = null;
let btnSurface = null;
let btnReset = null;
let mobileGuardEl = null;
let mobileExitBtn = null;

const pdbCache = new Map();

/**
 * Parse receptor & ligand polar atoms from first PDB model, filtering alternate locations cleanly.
 */
function parsePolarContacts(pdbText, target) {
  const receptorPolar = [];
  const ligandHet = [];
  const lines = pdbText.split(/\r?\n/);

  for (const line of lines) {
    if (line.startsWith('ENDMDL')) break;
    const isAtom = line.startsWith('ATOM  ');
    const isHet = line.startsWith('HETATM');
    if (!isAtom && !isHet) continue;

    const altLoc = line[16] || ' ';
    if (altLoc !== ' ' && altLoc !== 'A') continue;

    const atomName = line.slice(12, 16).trim();
    const resName = line.slice(17, 20).trim().toUpperCase();
    const resSeq = parseInt(line.slice(22, 26).trim(), 10);
    const x = parseFloat(line.slice(30, 38));
    const y = parseFloat(line.slice(38, 46));
    const z = parseFloat(line.slice(46, 54));
    if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue;

    const elemRaw = line.slice(76, 78).trim().toUpperCase();
    const elem = elemRaw || atomName.replace(/[^A-Za-z]/g, '').charAt(0).toUpperCase();
    if (elem !== 'N' && elem !== 'O') continue;

    if (isAtom) {
      receptorPolar.push({ resName, resSeq, atomName, x, y, z });
    } else {
      if (EXCLUDED_HETERO.has(resName)) continue;
      if (target && Array.isArray(target.ligandResns) && target.ligandResns.length > 0) {
        if (!target.ligandResns.includes(resName)) continue;
      }
      ligandHet.push({ resName, resSeq, atomName, x, y, z });
    }
  }

  if (ligandHet.length === 0 || receptorPolar.length === 0) {
    return [];
  }

  const pairs = [];
  for (const lig of ligandHet) {
    for (const rec of receptorPolar) {
      const dx = lig.x - rec.x;
      const dy = lig.y - rec.y;
      const dz = lig.z - rec.z;
      const distSq = dx * dx + dy * dy + dz * dz;
      if (distSq >= 2.2 * 2.2 && distSq <= 3.5 * 3.5) {
        pairs.push({ lig, rec, dist: Math.sqrt(distSq) });
      }
    }
  }

  pairs.sort((a, b) => a.dist - b.dist);
  const selected = [];
  const seenResidues = new Set();
  for (const p of pairs) {
    const key = `${p.rec.resName}:${p.rec.resSeq}`;
    if (seenResidues.has(key)) continue;
    seenResidues.add(key);
    selected.push(p);
    if (selected.length >= 3) break;
  }
  return selected;
}

async function fetchPDBWithFallback(pdbId, seqId) {
  if (pdbCache.has(pdbId)) {
    return { pdbText: pdbCache.get(pdbId), source: 'cache' };
  }

  if (activeFetchController) {
    activeFetchController.abort();
  }
  const controller = new AbortController();
  activeFetchController = controller;

  if (scanOverlayEl) scanOverlayEl.classList.remove('hidden');

  let pdbText = null;
  let source = 'unavailable';

  try {
    const localRes = await fetch(`./data/pdbs/${pdbId}.pdb`, { signal: controller.signal });
    if (localRes.ok) {
      const text = await localRes.text();
      if (text && text.length > 100) {
        pdbText = text;
        source = 'local';
      }
    }
  } catch (err) {
    if (err && err.name === 'AbortError') return null;
  }

  if (!pdbText) {
    const timeoutId = setTimeout(() => controller.abort(), 4500);
    try {
      const res = await fetch(`https://files.rcsb.org/download/${pdbId}.pdb`, {
        signal: controller.signal
      });
      if (res.ok) {
        const text = await res.text();
        if (text && text.length > 100) {
          pdbText = text;
          source = 'rcsb';
        }
      }
    } catch (err) {
      if (err && err.name === 'AbortError') {
        console.warn(`[3D Pose Lab] Fetch aborted/timed out for ${pdbId}.`);
      }
    } finally {
      clearTimeout(timeoutId);
    }
  }

  if (seqId !== requestSeq) {
    return null;
  }

  if (pdbText) {
    pdbCache.set(pdbId, pdbText);
  }

  if (statusBadgeEl) {
    if (source === 'local') {
      statusBadgeEl.innerHTML = `<span class="badge-measured" style="background:rgba(255,138,76,0.15);color:#FF8A4C;border-color:rgba(255,138,76,0.3);">Local PDB Cache (${escapeHtml(pdbId)})</span>`;
    } else if (source === 'rcsb') {
      statusBadgeEl.innerHTML = `<span class="badge-measured">RCSB Live PDB (${escapeHtml(pdbId)})</span>`;
    } else {
      statusBadgeEl.innerHTML = `<span class="badge-illustrative">Structure Unavailable Offline</span>`;
    }
  }

  if (scanOverlayEl) scanOverlayEl.classList.add('hidden');
  return { pdbText, source };
}

function renderComplex(pdbText, target) {
  if (!viewer || !pdbText) return;

  viewer.clear();
  isSurfaceActive = false;
  surfaceObj = null;
  if (btnSurface) btnSurface.classList.remove('active');

  viewer.addModel(pdbText, 'pdb');

  viewer.setStyle({ model: 0 }, {
    cartoon: {
      color: '#5CE1FF',
      opacity: 0.78,
      thickness: 0.4
    }
  });

  if (target.pocketResidues && target.pocketResidues.length > 0) {
    viewer.setStyle(
      { model: 0, resi: target.pocketResidues },
      {
        cartoon: { color: '#10B981', opacity: 0.95 },
        stick: { colorscheme: 'cyanCarbon', radius: 0.18 }
      }
    );
  }

  viewer.setStyle(
    { model: 0, hetflag: true },
    {
      stick: { colorscheme: 'greenCarbon', radius: 0.28 }
    }
  );

  // Render strictly measured crystallographic polar contacts (2.2 <= d <= 3.5 A)
  try {
    const contacts = parsePolarContacts(pdbText, target);
    contacts.forEach((c, idx) => {
      viewer.addCylinder({
        start: { x: c.lig.x, y: c.lig.y, z: c.lig.z },
        end: { x: c.rec.x, y: c.rec.y, z: c.rec.z },
        radius: 0.08,
        color: idx === 0 ? '#facc15' : '#5CE1FF',
        dashed: true
      });
      if (idx === 0) {
        const mid = {
          x: (c.lig.x + c.rec.x) * 0.5,
          y: (c.lig.y + c.rec.y) * 0.5,
          z: (c.lig.z + c.rec.z) * 0.5
        };
        const resLabel = `${c.rec.resName.charAt(0)}${c.rec.resName.slice(1).toLowerCase()}${c.rec.resSeq}`;
        viewer.addLabel(`${resLabel} H-Bond (${c.dist.toFixed(2)} Å)`, {
          position: mid,
          backgroundColor: 'rgba(5,7,10,0.85)',
          fontColor: '#facc15',
          fontSize: 11,
          showBackground: true
        });
      }
    });
  } catch (e) {
    console.warn('[3D Pose Lab] Contact rendering skipped:', e);
  }

  viewer.zoomTo();
  viewer.render();
  if (containerEl) {
    containerEl.classList.add('is-ready');
  }

  if (isRotating) {
    viewer.spin('y', 1);
  }

  window.dispatchEvent(new CustomEvent('bionemo:target-changed', { detail: target }));
}

export async function setTarget(pdbId) {
  if (!TARGET_REGISTRY[pdbId]) return;
  const seqId = ++requestSeq;
  currentTargetId = pdbId;
  const target = TARGET_REGISTRY[pdbId];

  targetPillBtns.forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-target-pdb') === pdbId);
  });

  const result = await fetchPDBWithFallback(pdbId, seqId);
  if (!result || seqId !== requestSeq || !result.pdbText) return;
  renderComplex(result.pdbText, target);
}

export function toggleSurface() {
  if (!viewer || typeof $3Dmol === 'undefined') return;
  isSurfaceActive = !isSurfaceActive;

  if (btnSurface) {
    btnSurface.classList.toggle('active', isSurfaceActive);
  }

  if (isSurfaceActive) {
    surfaceObj = viewer.addSurface($3Dmol.SurfaceType.VDW, {
      opacity: 0.38,
      color: '#5CE1FF'
    }, { model: 0 });
  } else if (surfaceObj) {
    viewer.removeSurface(surfaceObj);
    surfaceObj = null;
  }
  viewer.render();
}

export function focusPocket() {
  if (!viewer) return;
  const target = TARGET_REGISTRY[currentTargetId];
  if (target && target.pocketResidues) {
    viewer.zoomTo({ resi: target.pocketResidues }, 600);
  } else {
    viewer.zoomTo({ hetflag: true }, 600);
  }
}

export function toggleRotation() {
  if (!viewer) return;
  isRotating = !isRotating;
  if (btnRotate) btnRotate.classList.toggle('active', isRotating);
  viewer.spin(isRotating ? 'y' : false, 1);
}

export function resetCamera() {
  if (!viewer) return;
  viewer.zoomTo();
  viewer.render();
  if (containerEl) {
    containerEl.classList.add('is-ready');
  }
}

async function init() {
  containerEl = document.getElementById('molViewer3D');
  if (!containerEl) return;

  scanOverlayEl = document.getElementById('pose-scan-overlay');
  statusBadgeEl = document.getElementById('pose-source-badge');

  if (typeof $3Dmol === 'undefined') {
    if (cdnRetryCount < MAX_CDN_RETRIES) {
      cdnRetryCount += 1;
      setTimeout(init, 200);
    } else {
      if (scanOverlayEl) scanOverlayEl.classList.add('hidden');
      if (statusBadgeEl) {
        statusBadgeEl.innerHTML = `<span class="badge-illustrative">3D Engine Offline</span>`;
      }
      containerEl.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;padding:2rem;text-align:center;color:var(--color-ink-secondary);font-family:var(--font-mono);font-size:0.85rem;">WebGL 3Dmol.js library unavailable offline. Interactive telemetry cards remain active.</div>`;
    }
    return;
  }

  targetPillBtns = Array.from(document.querySelectorAll('.target-switch-pill'));
  btnRotate = document.getElementById('btn-pose-rotate');
  btnFocus = document.getElementById('btn-pose-focus');
  btnSurface = document.getElementById('btn-pose-surface');
  btnReset = document.getElementById('btn-pose-reset');
  mobileGuardEl = document.getElementById('mobile-touch-guard');
  mobileExitBtn = document.getElementById('btn-mobile-exit-3d');

function getThemeCanvasColor() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? '#F8FAFC' : '#0B0E14';
}

let viewerInitialized = false;

  containerEl.innerHTML = '';
  viewer = $3Dmol.createViewer(containerEl, {
    backgroundColor: getThemeCanvasColor(),
    antialias: true,
    defaultcolors: $3Dmol.rasmolElementColors
  });

  window.addEventListener('bionemo:theme-changed', () => {
    if (viewer) {
      try {
        viewer.setBackgroundColor(getThemeCanvasColor());
        viewer.render();
      } catch (_) {}
    }
  });

  targetPillBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      setTarget(btn.getAttribute('data-target-pdb'));
    });
  });

  if (btnRotate) btnRotate.addEventListener('click', toggleRotation);
  if (btnFocus) btnFocus.addEventListener('click', focusPocket);
  if (btnSurface) btnSurface.addEventListener('click', toggleSurface);
  if (btnReset) btnReset.addEventListener('click', resetCamera);

  if (mobileGuardEl) {
    mobileGuardEl.addEventListener('click', () => {
      mobileGuardEl.classList.add('unlocked');
      if (mobileExitBtn) mobileExitBtn.classList.add('active');
    });
  }
  if (mobileExitBtn) {
    mobileExitBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (mobileGuardEl) mobileGuardEl.classList.remove('unlocked');
      mobileExitBtn.classList.remove('active');
    });
  }

  await setTarget('8AZV');
}

function scheduleLazyInit() {
  const stage = document.getElementById('molViewer3D') || document.getElementById('pose-lab');
  if (!stage || typeof IntersectionObserver === 'undefined') {
    init();
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries.some((entry) => entry.isIntersecting);
      if (visible && !viewerInitialized) {
        viewerInitialized = true;
        init();
        return;
      }
      if (viewer) {
        viewer.spin(visible && isRotating ? 'y' : false, 1);
      }
    },
    { rootMargin: '250px' }
  );
  observer.observe(stage);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', scheduleLazyInit);
} else {
  scheduleLazyInit();
}

window.BioNeMoPoseLab = {
  setTarget,
  focusPocket,
  toggleRotation,
  toggleSurface,
  resetCamera,
  getTargetInfo: (id) => TARGET_REGISTRY[id || currentTargetId]
};
