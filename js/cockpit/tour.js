/**
 * 5-Step Developer Quickstart Engine for BioNeMo Cockpit (Non-modal <dialog>).
 */

import { state } from './state.js';
import { showToast, updateTargetInfo, selectLead } from './ui-controls.js';
import { open3DModal } from './viewer3d.js';
import { runDiscovery } from './api.js';
import { generateRobotProtocol } from './exports.js';
import { openModalDialog, closeModalDialog } from '../shared/dom-utils.js';

export const TOUR_STEPS = [
  {
    step: 1,
    title: '1/5: Select Target Complex',
    techBadge: 'Presets / RCSB / ESMFold',
    whatIs: 'Choose one of 16 curated benchmark complexes, fetch a crystal structure by 4-char RCSB PDB ID, or supply a FASTA sequence for ESMFold.',
    whatToDo: 'Click "Run Step" to load KRAS G12D (7RPZ) and inspect its Switch-II pocket coordinates.',
    action: () => {
      const select = document.getElementById('targetSelect');
      if (select) {
        select.value = '7RPZ';
        updateTargetInfo();
      }
      showToast('Loaded KRAS G12D (PDB: 7RPZ).');
    }
  },
  {
    step: 2,
    title: '2/5: Run Discovery Pipeline',
    techBadge: 'Council & ADMET',
    whatIs: 'Executes target profiling, scaffold generation, RDKit PAINS/BRENK/BOILED-Egg screening, and docking, updating all 4 KPI tiles.',
    whatToDo: 'Click "Run Step" to execute the pipeline and populate candidate leads.',
    action: () => {
      runDiscovery();
    }
  },
  {
    step: 3,
    title: '3/5: Inspect 3D Pose & Contacts',
    techBadge: '3Dmol.js & Plausibility',
    whatIs: 'Switch between docked poses, verify bond/clash/planarity/ΔE_strain checks, and click H-bond, salt-bridge, or π-stacking contact chips.',
    whatToDo: 'Click "Run Step" to select the top candidate and open the expanded 3D pocket inspector.',
    action: () => {
      if (state.currentLeads && state.currentLeads.length > 0) {
        selectLead(0);
      }
      open3DModal();
    }
  },
  {
    step: 4,
    title: '4/5: Chemical Workbench Re-Dock',
    techBadge: 'RDKit Bioisosteres',
    whatIs: 'Edit SMILES or apply single-click substitutions (+F, +Me, pyridine swap) to recompute QED, SAScore, and ΔG.',
    whatToDo: 'Click "Run Step" to focus the Chemical Workbench SMILES editor.',
    action: () => {
      const wb = document.getElementById('workbenchCard') || document.getElementById('workbenchSmilesInput');
      if (wb) wb.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const input = document.getElementById('workbenchSmilesInput');
      if (input) input.focus();
    }
  },
  {
    step: 5,
    title: '5/5: Export Protocol & Dossier',
    techBadge: 'OT-2 & PDF Dossier',
    whatIs: 'Inspect the depth-3 binary BRICS synthesis tree and export Opentrons OT-2 liquid-handling scripts or ReportLab IND briefings.',
    whatToDo: 'Click "Run Step" to preview the executable Opentrons OT-2 synthesis protocol.',
    action: () => {
      generateRobotProtocol();
    }
  }
];

let keyHandlerBound = false;

export function startInteractiveTour() {
  state.currentTourStep = 0;
  const modal = document.getElementById('tourCardModal');
  if (modal) {
    openModalDialog(modal, { nonModal: true });
    if (!modal.dataset.cancelBound) {
      modal.dataset.cancelBound = '1';
      modal.addEventListener('cancel', (e) => {
        e.preventDefault();
        closeInteractiveTour();
      });
    }
  }
  if (!keyHandlerBound) {
    keyHandlerBound = true;
    window.addEventListener('keydown', (e) => {
      const m = document.getElementById('tourCardModal');
      if (!m || !m.open) return;
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        nextTourStep();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        prevTourStep();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        closeInteractiveTour();
      }
    });
  }
  renderTourStep(0);
}

export function closeInteractiveTour() {
  try { localStorage.setItem('bionemo_guide_seen', 'true'); } catch (_) {}
  closeModalDialog(document.getElementById('tourCardModal'));
}

export function renderTourStep(index) {
  if (index < 0 || index >= TOUR_STEPS.length) return;
  state.currentTourStep = index;
  const step = TOUR_STEPS[index];

  const badge = document.getElementById('tourStepBadge');
  const techBadge = document.getElementById('tourTechBadge');
  const progBar = document.getElementById('tourProgressBar');
  const title = document.getElementById('tourStepTitle');
  const whatIs = document.getElementById('tourWhatIs');
  const whatToDo = document.getElementById('tourWhatToDo');
  const btnPrev = document.getElementById('btnTourPrev');
  const btnNext = document.getElementById('btnTourNext');

  if (badge) badge.textContent = `Step ${step.step} of ${TOUR_STEPS.length}`;
  if (techBadge) techBadge.textContent = step.techBadge;
  if (progBar) progBar.style.width = `${((index + 1) / TOUR_STEPS.length) * 100}%`;
  if (title) title.textContent = step.title;
  if (whatIs) whatIs.textContent = step.whatIs;
  if (whatToDo) whatToDo.textContent = step.whatToDo;

  if (btnPrev) {
    btnPrev.disabled = index === 0;
    btnPrev.style.opacity = index === 0 ? '0.4' : '1.0';
    btnPrev.style.cursor = index === 0 ? 'not-allowed' : 'pointer';
  }

  if (btnNext) {
    btnNext.textContent = index === TOUR_STEPS.length - 1 ? 'Finish' : 'Next Step →';
  }
}

export function nextTourStep() {
  if (state.currentTourStep >= TOUR_STEPS.length - 1) {
    closeInteractiveTour();
    return;
  }
  renderTourStep(state.currentTourStep + 1);
}

export function prevTourStep() {
  if (state.currentTourStep <= 0) return;
  renderTourStep(state.currentTourStep - 1);
}

export function executeTourAction() {
  const step = TOUR_STEPS[state.currentTourStep];
  if (step && typeof step.action === 'function') {
    step.action();
  }
}
