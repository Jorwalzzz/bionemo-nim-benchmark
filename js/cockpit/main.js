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
  queryRcsbMetadata,
  onCustomTargetInput,
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
  sleep,
  updateProvenanceBanner,
  openRawReceiptModal,
  closeRawReceiptModal,
  copyRawReceiptJson,
  exportActiveRunJson
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
  openStaticDemoModal,
  closeStaticDemoModal,
  closeAllModals
} from './modals.js';

import {
  initOwnerAccess,
  openOwnerModal,
  closeOwnerModal,
  submitOwnerLogin,
  handleOwnerLogout,
  isOwner
} from './owner-auth.js';

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
  queryRcsbMetadata,
  onCustomTargetInput,
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
  openOwnerModal,
  closeOwnerModal,
  submitOwnerLogin,
  handleOwnerLogout,
  checkIsOwner: isOwner,
  generateINDPdf,
  generateRobotProtocol,
  generateLabCard,
  openRobotModal,
  closeRobotModal,
  openRawReceiptModal,
  closeRawReceiptModal,
  copyRawReceiptJson,
  updateProvenanceBanner,
  exportActiveRunJson,
  openStaticDemoModal,
  closeStaticDemoModal,
  updateHeaderAuthUI,
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

// ─── Header Auth / Static Mode UI ─────────────────────────────────────────
export function updateHeaderAuthUI(forceStatic = false) {
  const isLoopback = !forceStatic && typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  const authHud = document.getElementById('authHudContainer');
  const staticDemo = document.getElementById('staticDemoContainer');
  const ownerAccess = document.getElementById('ownerAccessContainer');

  if (!isLoopback) {
    if (authHud) {
      authHud.style.display = 'none';
      authHud.classList.add('hidden');
    }
    if (staticDemo) {
      staticDemo.style.display = 'flex';
      staticDemo.classList.remove('hidden');
    }
    if (ownerAccess) {
      ownerAccess.style.display = 'none';
      ownerAccess.classList.add('hidden');
    }
  } else {
    if (authHud) {
      authHud.style.display = 'flex';
      authHud.classList.remove('hidden');
    }
    if (staticDemo) {
      staticDemo.style.display = 'none';
      staticDemo.classList.add('hidden');
    }
  }
}

// ─── Cockpit Lifecycle Initialization ────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  updateHeaderAuthUI();
  initOwnerAccess();
  fetchTrialStatus();

  // Instant 3D Structure Render for Default Target via telemetry sync & PDB loader
  updateTargetInfo();

  // Clean Idle Launch State (zero fake preloaded leads, KPI metrics idle, empty Pareto)
  state.currentLeads = [];
  state.currentSelectedLead = null;
  renderLeads();
  renderPareto();
  const kpiAff = document.getElementById('kpiAffinity');
  if (kpiAff) kpiAff.textContent = '—';
  const kpiQed = document.getElementById('kpiQed');
  if (kpiQed) kpiQed.textContent = '—';
  const kpiSc = document.getElementById('kpiScreened');
  if (kpiSc) kpiSc.textContent = '—';
  const kpiPar = document.getElementById('kpiPareto');
  if (kpiPar) kpiPar.textContent = '—';

  updateProvenanceBanner({
    mode: 'OFFLINE_DEMO',
    provenance: 'SIMULATED',
    backend_host: window.location.hostname || 'localhost',
    timestamp_utc: new Date().toISOString(),
    notice: 'Idle standby mode. Select a target and run autonomous discovery to begin.'
  });

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

if (typeof window !== 'undefined' && typeof window.isOwner !== 'boolean') {
  window.isOwner = false;
}

// ─── CSP-Compliant Delegated UI Event Dispatcher ─────────────────────────────
function dispatchAction(action, el, event) {
  switch (action) {
    case 'start-tour': return startInteractiveTour();
    case 'close-tour': return closeInteractiveTour();
    case 'tour-prev': return prevTourStep();
    case 'tour-action': return executeTourAction();
    case 'tour-next': return nextTourStep();
    case 'open-benchmark-modal': return openBenchmarkModal();
    case 'close-benchmark-modal': return closeBenchmarkModalDirect();
    case 'run-live-benchmark': return runLiveBenchmark();
    case 'open-feedback-modal': return openFeedbackModal();
    case 'close-feedback-modal': return closeFeedbackModal();
    case 'open-static-demo-modal': return openStaticDemoModal();
    case 'close-static-demo-modal': return closeStaticDemoModal();
    case 'open-auth-modal': return openAuthModal(el.dataset.arg || undefined);
    case 'close-auth-modal': return closeAuthModal();
    case 'switch-auth-tab': return switchAuthTab(el.dataset.arg);
    case 'demo-login': return handleDemoLogin();
    case 'logout': return handleLogout();
    case 'open-install-modal': return openInstallModal();
    case 'close-install-modal': return closeInstallModal();
    case 'open-quota-and-install':
      closeQuotaModal();
      return openInstallModal();
    case 'close-quota-modal': return closeQuotaModal();
    case 'open-owner-modal': return openOwnerModal();
    case 'close-owner-modal': return closeOwnerModal();
    case 'submit-owner-login': return submitOwnerLogin();
    case 'switch-target-tab': return switchTargetTab(el.dataset.arg);
    case 'fetch-custom-target': return fetchCustomTarget();
    case 'load-esm-preset': return loadEsmPreset(el.dataset.arg);
    case 'fold-denovo': return foldDeNovoSequence();
    case 'set-rounds': return setRounds(parseInt(el.dataset.arg || '2', 10));
    case 'run-discovery': return runDiscovery();
    case 'open-raw-receipt': return openRawReceiptModal();
    case 'close-raw-receipt': return closeRawReceiptModal();
    case 'copy-raw-receipt': return copyRawReceiptJson();
    case 'export-run-json': return exportActiveRunJson();
    case 'open-3d-modal': return open3DModal();
    case 'close-3d-modal': return close3DModalDirect();
    case 'toggle-3d-spin': return toggle3DSpin();
    case 'toggle-3d-surface': return toggle3DSurface();
    case 'reset-3d-view': return reset3DView();
    case 'close-resistance-modal': return closeResistanceModal();
    case 'copy-evolved-smiles': return copyEvolvedSmiles();
    case 'adopt-evolved-scaffold': return adoptEvolvedScaffold();
    case 'close-robot-modal': return closeRobotModal();
    case 'copy-ot2-code': return copyOT2Code();
    case 'download-ot2-py': return downloadCurrentOT2Py();
    case 'lab-card': return generateLabCard();
    case 'robot-protocol': return generateRobotProtocol();
    case 'resistance-test': return runResistanceStressTest();
    case 'generate-ind-pdf': return generateINDPdf();
    case 'download-dossier': return downloadDossier();
    case 'download-sdf': return downloadSDF();
    case 'select-lead': return selectLead(parseInt(el.dataset.leadIndex || '0', 10));
    case 'load-wb-preset': return loadWorkbenchPreset(el.dataset.arg);
    case 'tweak-smiles': return tweakSmiles(el.dataset.arg);
    case 'trigger-redock': return triggerRedockFromWorkbench();
    default: return undefined;
  }
}

document.addEventListener('click', (e) => {
  if (e.target && e.target.hasAttribute && e.target.hasAttribute('data-backdrop-close')) {
    dispatchAction(e.target.getAttribute('data-backdrop-close'), e.target, e);
    return;
  }
  const trigger = e.target?.closest ? e.target.closest('[data-action]') : null;
  if (trigger) {
    dispatchAction(trigger.getAttribute('data-action'), trigger, e);
  }
});

document.addEventListener('change', (e) => {
  const trigger = e.target?.closest ? e.target.closest('[data-change-action]') : null;
  if (!trigger) return;
  if (trigger.getAttribute('data-change-action') === 'update-target-info') {
    updateTargetInfo();
  }
});

document.addEventListener('input', (e) => {
  const el = e.target?.closest ? e.target.closest('[data-input-action]') : null;
  if (!el) return;
  const act = el.getAttribute('data-input-action');
  if (act === 'custom-target-input') {
    onCustomTargetInput(el.value);
  } else if (act === 'update-seq-count') {
    updateSeqCount();
  } else if (act === 'candidate-slider') {
    const numEl = document.getElementById('candidateNum');
    if (numEl) numEl.textContent = el.value;
  } else if (act === 'email-validation') {
    handleEmailInputValidation(el, el.getAttribute('data-feedback-id') || '');
  } else if (act === 'workbench-input') {
    onWorkbenchInput(el.value);
  }
});

document.addEventListener('submit', (e) => {
  const form = e.target;
  if (!form || !form.getAttribute) return;
  const act = form.getAttribute('data-submit-action');
  if (act === 'auth-login') handleAuthLogin(e);
  else if (act === 'auth-register') handleAuthRegister(e);
  else if (act === 'feedback-submit') handleFeedbackSubmit(e);
});

// ─── Universal Keyboard Listeners (Escape & Non-Native Card Triggers) ────────
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    closeAllModals();
    return;
  }
  if (e.key === 'Enter' && e.target?.getAttribute?.('data-enter-action') === 'submit-owner-login') {
    submitOwnerLogin();
    return;
  }
  if ((e.key === 'Enter' || e.key === ' ') && e.target?.getAttribute?.('data-action') === 'select-lead') {
    e.preventDefault();
    selectLead(parseInt(e.target.getAttribute('data-lead-index') || '0', 10));
  }
});
