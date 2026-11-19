/**
 * Cockpit ES Module Entrypoint.
 * Imports modules, synchronizes reactive state with window, attaches all interactive
 * handlers to window for HTML inline attribute compatibility, and initializes lifecycle.
 */

import {
  state,
  isStaticHost,
  isLocalServer,
  ESMFOLD_PRESETS,
  PRESET_INHIBITORS,
  TARGETS,
  EMPIRICAL_TARGET_LEADS
} from './state.js';

import {
  pdbCache,
  loadPdb,
  primaryViewer,
  modalViewer,
  is3DSpinning,
  is3DSurfaceOn,
  surfaceObj,
  currentPoseSdf,
  init3DViewer,
  render3DComplex,
  toggle3DSpin,
  toggle3DSurface,
  reset3DView,
  open3DModal,
  close3DModal,
  close3DModalDirect,
  updateLead3DView,
  generateClientDeNovoPdb,
  foldDeNovoSequence,
  fetchCustomTarget,
  evaluateClientRedock,
  triggerRedockFromWorkbench,
  redockModifiedLead
} from './viewer3d.js';

import {
  paretoChart,
  renderPareto,
  runLiveBenchmark
} from './charts.js';

import {
  getClientFingerprint,
  computeISTCycleInfo,
  validateEmailDetailed,
  handleEmailInputValidation,
  fixEmailTypo,
  escapeHtml,
  hashPasswordSHA256,
  ClientAuthManager,
  clientAuth,
  resetTrialQuota,
  _qSig,
  staticQuota,
  fetchTrialStatus,
  updateTrialUI,
  runDiscovery
} from './api.js';

import {
  setRounds,
  switchTargetTab,
  updateSeqCount,
  loadEsmPreset,
  onWorkbenchInput,
  loadWorkbenchPreset,
  tweakSmiles,
  updateTargetInfo,
  setAgent,
  resetAgents,
  logEntry,
  renderLeads,
  selectLead,
  switchTab,
  copyCode,
  showToast,
  sleep
} from './ui-controls.js';

import {
  openAuthModal,
  closeAuthModal,
  switchAuthTab,
  handleAuthLogin,
  handleDemoLogin,
  handleAuthRegister,
  handleLogout,
  openQuotaModal,
  closeQuotaModal,
  openFeedbackModal,
  closeFeedbackModal,
  renderFeedbackHistory,
  handleFeedbackSubmit,
  openInstallModal,
  closeInstallModal,
  closeModalOnBackdrop,
  openBenchmarkModal,
  closeBenchmarkModal,
  closeBenchmarkModalDirect,
  openRobotModal,
  closeRobotModal,
  openResistanceModal,
  closeResistanceModal,
  closeAllModals
} from './modals.js';

import {
  downloadInstaller,
  downloadDossier,
  downloadSDF,
  generateINDPdf,
  downloadIndPdf,
  generateRobotProtocol,
  generateLabCard,
  downloadCurrentOT2Py,
  copyOT2Code,
  runResistanceStressTest,
  adoptEvolvedScaffold,
  copyEvolvedSmiles
} from './exports.js';

import {
  TOUR_STEPS,
  startInteractiveTour,
  closeInteractiveTour,
  renderTourStep,
  nextTourStep,
  prevTourStep,
  executeTourAction
} from './tour.js';

// Anti-clickjacking / framing sentinel
if (window.top !== window.self) {
  try {
    window.top.location = window.self.location;
  } catch (e) {
    document.documentElement.innerHTML = '';
  }
}

// Expose all interactive functions and state objects to window for inline onclick attributes
Object.assign(window, {
  // State & Constants
  isStaticHost,
  isLocalServer,
  ESMFOLD_PRESETS,
  PRESET_INHIBITORS,
  TARGETS,
  EMPIRICAL_TARGET_LEADS,
  TOUR_STEPS,
  
  // 3D Visualizer & Biophysics
  pdbCache,
  loadPdb,
  init3DViewer,
  render3DComplex,
  toggle3DSpin,
  toggle3DSurface,
  reset3DView,
  open3DModal,
  close3DModal,
  close3DModalDirect,
  updateLead3DView,
  generateClientDeNovoPdb,
  foldDeNovoSequence,
  fetchCustomTarget,
  evaluateClientRedock,
  triggerRedockFromWorkbench,
  redockModifiedLead,

  // Charts & Benchmarks
  renderPareto,
  runLiveBenchmark,

  // API, Auth, Quota & Discovery
  getClientFingerprint,
  computeISTCycleInfo,
  validateEmailDetailed,
  handleEmailInputValidation,
  fixEmailTypo,
  escapeHtml,
  hashPasswordSHA256,
  ClientAuthManager,
  clientAuth,
  resetTrialQuota,
  _qSig,
  staticQuota,
  fetchTrialStatus,
  updateTrialUI,
  runDiscovery,
  runCampaign: runDiscovery,

  // UI Controls, Modals & Workflows
  setRounds,
  switchTargetTab,
  updateSeqCount,
  loadEsmPreset,
  onWorkbenchInput,
  loadWorkbenchPreset,
  tweakSmiles,
  openAuthModal,
  closeAuthModal,
  switchAuthTab,
  handleAuthLogin,
  handleDemoLogin,
  handleAuthRegister,
  handleLogout,
  openQuotaModal,
  closeQuotaModal,
  openFeedbackModal,
  closeFeedbackModal,
  renderFeedbackHistory,
  handleFeedbackSubmit,
  updateTargetInfo,
  setAgent,
  resetAgents,
  logEntry,
  renderLeads,
  selectLead,
  openInstallModal,
  closeInstallModal,
  closeModalOnBackdrop,
  switchTab,
  copyCode,
  showToast,
  downloadInstaller,
  downloadDossier,
  downloadSDF,
  sleep,
  openBenchmarkModal,
  closeBenchmarkModal,
  closeBenchmarkModalDirect,
  generateINDPdf,
  generateRobotProtocol,
  generateLabCard,
  openRobotModal,
  closeRobotModal,
  downloadCurrentOT2Py,
  copyOT2Code,
  runResistanceStressTest,
  openResistanceModal,
  closeResistanceModal,
  adoptEvolvedScaffold,
  copyEvolvedSmiles,
  startInteractiveTour,
  closeInteractiveTour,
  renderTourStep,
  nextTourStep,
  prevTourStep,
  executeTourAction,
  closeAllModals
});

// ─── Cybernetic Bios Boot Sequence ───────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const bootloader = document.getElementById("biosBootloader");
  if (!bootloader) return;

  const steps = [
    { id: "bootLine1", pct: 25, label: "Connecting NVIDIA NIM endpoints..." },
    { id: "bootLine2", pct: 50, label: "Calibrating 3Dmol WebGL Engine..." },
    { id: "bootLine3", pct: 75, label: "Mounting RDKit MedChem Veto Rules..." },
    { id: "bootLine4", pct: 90, label: "Synchronizing Robot Protocol Generators..." },
    { id: "bootLine5", pct: 100, label: "All Swarm Sub-Agents Online!" }
  ];

  let currentStep = 0;
  const interval = setInterval(() => {
    if (currentStep < steps.length) {
      const step = steps[currentStep];
      const el = document.getElementById(step.id);
      if (el) el.classList.remove("opacity-0");
      const bar = document.getElementById("bootProgressBar");
      if (bar) bar.style.width = step.pct + "%";
      const pct = document.getElementById("bootProgressPct");
      if (pct) pct.textContent = step.pct + "%";
      const lbl = document.getElementById("bootProgressLabel");
      if (lbl) lbl.textContent = step.label;
      currentStep++;
    } else {
      clearInterval(interval);
      setTimeout(() => {
        bootloader.style.opacity = "0";
        setTimeout(() => {
          bootloader.remove();
        }, 700);
      }, 400);
    }
  }, 220);
});

// ─── Cockpit Lifecycle Initialization ────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  fetchTrialStatus();

  // Instant 3D Structure Render for Default Target (KRAS G12D / 8AZV) via on-demand PDB fetch
  const pdbText = await loadPdb('8AZV');
  if (pdbText) {
    state.currentTargetPdbText = pdbText;
    state.currentTargetPocketResidues = ['GLY12', 'ASP12', 'GLN61', 'TYR96'];
    render3DComplex(state.currentTargetPdbText, null, state.currentTargetPocketResidues, false, 94.5);
    if (primaryViewer) {
      primaryViewer.spin('y', 0.5);
    }
  }

  // Pre-load authentic empirical benchmark leads for instant interactive dashboard display
  if (!state.currentLeads || state.currentLeads.length === 0) {
    const defaultLeads = EMPIRICAL_TARGET_LEADS['KRAS G12D'] || [];
    state.currentLeads = defaultLeads.slice(0, 5).map((lead, idx) => ({
      ...lead,
      round: idx < 3 ? 1 : 2
    }));
    renderLeads();
    renderPareto();
    const topLead = state.currentLeads[0];
    if (topLead) {
      const kpiAff = document.getElementById('kpiAffinity');
      if (kpiAff) kpiAff.textContent = topLead.affinity.toFixed(2);
      const kpiQed = document.getElementById('kpiQed');
      if (kpiQed) kpiQed.textContent = topLead.qed.toFixed(3);
      const kpiSc = document.getElementById('kpiScreened');
      if (kpiSc) kpiSc.textContent = state.currentLeads.length;
      const kpiPar = document.getElementById('kpiPareto');
      if (kpiPar) kpiPar.textContent = state.currentLeads.filter(l => l.pareto).length;
    }
  }

  // Auto-launch Guide once for first-time visitors
  try {
    const hasSeenGuide = localStorage.getItem('bionemo_guide_seen');
    if (!hasSeenGuide) {
      setTimeout(() => {
        startInteractiveTour();
      }, 1000);
    }
  } catch (e) {
    console.warn('LocalStorage error:', e);
  }
});

// ─── Universal Escape Key Listener ───────────────────────────────────────────
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    closeAllModals();
  }
});
