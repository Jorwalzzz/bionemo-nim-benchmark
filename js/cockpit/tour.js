/**
 * Interactive 10-Step Guided Tour Engine for BioNeMo Cockpit.
 */

import { state } from './state.js';
import { showToast, updateTargetInfo, selectLead } from './ui-controls.js';
import { openBenchmarkModal, openResistanceModal } from './modals.js';
import { open3DModal, toggle3DSpin } from './viewer3d.js';
import { runDiscovery } from './api.js';
import { generateRobotProtocol, downloadIndPdf } from './exports.js';

export const TOUR_STEPS = [
  {
    step: 1,
    title: '1/10: 3-Panel Discovery Studio',
    techBadge: 'Architecture',
    whatIs: '• Left: Target selection & AI Council Swarm\n• Center: Multi-Agent Thought Stream & Pareto Frontier\n• Right: Live Clinical Lead Dossier & 3D Inspector',
    whatToDo: 'Glance across the 3 columns to see how biology, 3D biophysics, and chemistry synchronize.',
    action: () => {
      showToast('🧭 Highlighting 3-Panel Discovery Studio.');
      const aside = document.querySelector('aside');
      if (aside) aside.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  },
  {
    step: 2,
    title: '2/10: Hardware Speedup Benchmark',
    techBadge: 'NVIDIA H100 vs CPU',
    whatIs: '• Biomolecular AI takes hours on laptops\n• NVIDIA NIM on H100 delivers up to 54× acceleration in sub-seconds',
    whatToDo: 'Click "⚡ Try This Step" to open the live benchmark and compare your local CPU against H100 Tensor Cores.',
    action: () => {
      openBenchmarkModal();
    }
  },
  {
    step: 3,
    title: '3/10: Target Ingestion & ESMFold',
    techBadge: 'ESMFold & RCSB PDB',
    whatIs: '• Pick an oncology target, enter a PDB code, or paste a raw amino acid sequence\n• ESMFold predicts atomic 3D structures in seconds',
    whatToDo: 'Click "⚡ Try This Step" to auto-select KRAS G12D (PDB: 4OBE) with pocket druggability 0.84.',
    action: () => {
      const select = document.getElementById('targetSelect');
      if (select) {
        select.value = 'KRAS G12D';
        updateTargetInfo();
      }
      const aside = document.querySelector('aside');
      if (aside) aside.scrollTo({ top: 0, behavior: 'smooth' });
      showToast('🎯 Target set to KRAS G12D (PDB: 4OBE, Druggability: 0.84)');
    }
  },
  {
    step: 4,
    title: '4/10: Launch 6-Agent AI Council',
    techBadge: 'Autonomous Swarm',
    whatIs: '• 6 AI agents collaborate: Scout, Chemist, Critic, Docker, Planner, and Arbiter\n• Generates and screens novel small molecule leads',
    whatToDo: 'Click "⚡ Try This Step" (or the green "Launch Discovery" button) to watch the council stream real-time results.',
    action: () => {
      runDiscovery();
      showToast('🚀 Autonomous 6-Agent Council launched!');
    }
  },
  {
    step: 5,
    title: '5/10: Pareto Frontier & Top Lead',
    techBadge: 'Pareto Optimization',
    whatIs: '• Balances binding affinity (ΔG) against drug-likeness (QED)\n• Nominates the #1 lead candidate on the optimal frontier',
    whatToDo: 'Click "⚡ Try This Step" to highlight and select the highest-scoring candidate.',
    action: () => {
      if (state.currentLeads && state.currentLeads.length > 0) {
        selectLead(0);
        showToast(`🏆 Selected top nominated lead: ${state.currentLeads[0].id}`);
      } else {
        showToast('ℹ️ Launch the council in Step 4 first to generate candidate leads.');
      }
      const table = document.getElementById('leadsContainer');
      if (table) table.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  },
  {
    step: 6,
    title: '6/10: 3D Protein-Ligand Inspector',
    techBadge: '3Dmol.js WebGL',
    whatIs: '• Real-time 3D rendering of target binding pocket and docked ligand\n• Cyan sticks: active site | Green sticks: drug molecule',
    whatToDo: 'Click "⚡ Try This Step" to open the high-res 3D inspector with pocket surfaces and auto-rotation.',
    action: () => {
      open3DModal();
      toggle3DSpin();
      showToast('🔬 3D Inspector opened with auto-rotation.');
    }
  },
  {
    step: 7,
    title: '7/10: Chemical Workbench & Re-Docking',
    techBadge: 'RDKit & Bioisosteres',
    whatIs: '• Edit SMILES directly or click bioisosteric functional groups (F-swap, Me-cap)\n• Triggers instant DiffDock re-docking & Lipinski recalculation',
    whatToDo: 'Click "⚡ Try This Step" to focus the workbench and test an analog substitution.',
    action: () => {
      const wb = document.getElementById('workbenchCard') || document.getElementById('workbenchSmilesInput');
      if (wb) wb.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const input = document.getElementById('workbenchSmilesInput');
      if (input && (!input.value || input.value.trim() === '')) {
        input.value = 'COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1';
      }
      showToast('🧪 Chemical Workbench active: ready for bioisosteric edits.');
    }
  },
  {
    step: 8,
    title: '8/10: Adaptive Resistance Engine',
    techBadge: 'ESM-2 Counter-Design',
    whatIs: '• Predicts tumor escape mutations (e.g. G12D→G12V (steric resistance — illustrative))\n• MolMIM generates counter-measure scaffolds that retain potency',
    whatToDo: 'Click "⚡ Try This Step" to open the Resistance Engine and evolve an escape-resistant scaffold.',
    action: () => {
      openResistanceModal();
      showToast('🛡️ Resistance Engine opened.');
    }
  },
  {
    step: 9,
    title: '9/10: Opentrons OT-2 Robot Protocol',
    techBadge: 'Wet-Lab Robotics',
    whatIs: '• Converts computational designs into automated wet-lab synthesis\n• Generates ready-to-run Python code for Opentrons OT-2 robots & 96-well SOP cards',
    whatToDo: 'Click "⚡ Try This Step" to inspect and copy the executable liquid-handling protocol.',
    action: () => {
      generateRobotProtocol();
      showToast('🤖 Opentrons OT-2 protocol modal opened.');
    }
  },
  {
    step: 10,
    title: '10/10: Pre-Clinical Candidate Dossier',
    techBadge: 'ReportLab PDF Engine',
    whatIs: '• Compiles pharmacology, safety margins, and binding metrics into an official FDA briefing\n• Formats a complete multi-page regulatory PDF',
    whatToDo: 'Click "⚡ Try This Step" to download your Pre-Clinical Candidate Briefing Dossier (PDF).',
    action: () => {
      downloadIndPdf();
      showToast('📄 Downloading Pre-Clinical Candidate Briefing PDF...');
    }
  }
];

export function startInteractiveTour() {
  state.currentTourStep = 0;
  const modal = document.getElementById('tourCardModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'block';
  }
  renderTourStep(0);
}

export function closeInteractiveTour() {
  try { localStorage.setItem('bionemo_guide_seen', 'true'); } catch (e) {}
  const modal = document.getElementById('tourCardModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
  showToast('Guided tour closed. Click "🧭 Guide" anytime to resume.');
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

  if (badge) badge.textContent = `Step ${step.step} of 10`;
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
    if (index === TOUR_STEPS.length - 1) {
      btnNext.innerHTML = '<span>Finish Tour 🎉</span>';
    } else {
      btnNext.innerHTML = '<span>Next Step ➔</span>';
    }
  }
}

export function nextTourStep() {
  if (state.currentTourStep >= TOUR_STEPS.length - 1) {
    closeInteractiveTour();
    showToast('🎉 Tour completed! Enjoy using BioNeMo Autonomous Scientist.');
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
