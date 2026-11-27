/**
 * Cockpit Modal Dialog Handlers: Authentication, Quota, Feedback,
 * Hardware Benchmark, Robotics, Resistance, and 3D Viewers.
 */

import { state, TARGETS } from './state.js';
import { clientAuth, validateEmailDetailed, handleEmailInputValidation, escapeHtml, runDiscovery } from './api.js';
import { showToast, closeRawReceiptModal } from './ui-controls.js';
import { buildExportContext, buildStaticOt2Script } from './exports.js';
import { runLiveBenchmark } from './charts.js';
import { close3DModalDirect } from './viewer3d.js';
import { closeOwnerModal } from './owner-auth.js';
import { openModalDialog, closeModalDialog } from '../shared/dom-utils.js';

export function openAuthModal(noticeMessage) {
  const modal = document.getElementById('authModal');
  if (!modal) return;
  openModalDialog(modal);

  if (noticeMessage) {
    showToast(noticeMessage);
  }
  switchAuthTab('login');
}

export function closeAuthModal() {
  closeModalDialog(document.getElementById('authModal'));
}

export function switchAuthTab(tab) {
  const loginForm = document.getElementById('authLoginForm');
  const regForm = document.getElementById('authRegisterForm');
  const tabLogin = document.getElementById('authTabLogin');
  const tabReg = document.getElementById('authTabRegister');
  const errLogin = document.getElementById('authLoginError');
  const errReg = document.getElementById('authRegError');

  if (errLogin) { errLogin.textContent = ''; errLogin.classList.add('hidden'); }
  if (errReg) { errReg.textContent = ''; errReg.classList.add('hidden'); }

  if (tab === 'login') {
    if (loginForm) { loginForm.style.display = 'block'; loginForm.classList.remove('hidden'); }
    if (regForm) { regForm.style.display = 'none'; regForm.classList.add('hidden'); }
    if (tabLogin) { tabLogin.className = 'flex-1 py-1.5 text-xs font-bold rounded-md bg-emerald-600 text-white transition-all'; }
    if (tabReg) { tabReg.className = 'flex-1 py-1.5 text-xs font-semibold rounded-md text-gray-400 hover:text-white transition-all'; }
  } else {
    if (loginForm) { loginForm.style.display = 'none'; loginForm.classList.add('hidden'); }
    if (regForm) { regForm.style.display = 'block'; regForm.classList.remove('hidden'); }
    if (tabLogin) { tabLogin.className = 'flex-1 py-1.5 text-xs font-semibold rounded-md text-gray-400 hover:text-white transition-all'; }
    if (tabReg) { tabReg.className = 'flex-1 py-1.5 text-xs font-bold rounded-md bg-emerald-600 text-white transition-all'; }
  }
}

export async function handleAuthLogin(event) {
  if (event) event.preventDefault();
  const emailEl = document.getElementById('authLoginEmail');
  const pwdEl = document.getElementById('authLoginPassword');
  const errEl = document.getElementById('authLoginError');
  const btn = document.getElementById('authLoginSubmitBtn');

  const email = emailEl ? emailEl.value : '';
  const password = pwdEl ? pwdEl.value : '';

  const emailCheck = validateEmailDetailed(email);
  if (!emailCheck.valid && emailCheck.type === 'invalid') {
    if (errEl) {
      errEl.textContent = emailCheck.message;
      errEl.classList.remove('hidden');
    }
    if (emailEl) emailEl.focus();
    return;
  }

  if (btn) { btn.disabled = true; btn.textContent = 'Verifying credentials...'; }
  if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }

  const res = await clientAuth.login(email, password);
  if (btn) { btn.disabled = false; btn.textContent = 'Sign In to Workspace'; }

  if (res.success) {
    closeAuthModal();
    showToast(`Welcome back, ${res.user.full_name || res.user.email} (5 runs/day active).`);
    if (clientAuth.pendingAction === 'feedback') {
      clientAuth.pendingAction = null;
      openFeedbackModal();
    } else if (clientAuth.pendingAction === 'discovery') {
      clientAuth.pendingAction = null;
      runDiscovery();
    }
  } else {
    if (errEl) {
      errEl.textContent = res.message || 'Login failed. Please check credentials.';
      errEl.classList.remove('hidden');
    }
  }
}

export async function handleDemoLogin() {
  const errEl = document.getElementById('authLoginError');
  if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }

  const res = await clientAuth.demoLogin();
  if (res.success) {
    closeAuthModal();
    showToast('1-Click Reviewer Access granted: evaluator@bionemo.org');
    if (clientAuth.pendingAction === 'feedback') {
      clientAuth.pendingAction = null;
      openFeedbackModal();
    } else if (clientAuth.pendingAction === 'discovery') {
      clientAuth.pendingAction = null;
      runDiscovery();
    }
  } else {
    showToast('Demo login failed. Please try again.');
  }
}

export async function handleAuthRegister(event) {
  if (event) event.preventDefault();
  const nameEl = document.getElementById('authRegName');
  const orgEl = document.getElementById('authRegOrg');
  const emailEl = document.getElementById('authRegEmail');
  const pwdEl = document.getElementById('authRegPassword');
  const errEl = document.getElementById('authRegError');
  const btn = document.getElementById('authRegSubmitBtn');

  const name = nameEl ? nameEl.value : '';
  const org = orgEl ? orgEl.value : '';
  const email = emailEl ? emailEl.value : '';
  const password = pwdEl ? pwdEl.value : '';

  const emailCheck = validateEmailDetailed(email);
  if (!emailCheck.valid) {
    if (errEl) {
      errEl.textContent = emailCheck.message;
      errEl.classList.remove('hidden');
    }
    if (emailEl) {
      emailEl.focus();
      handleEmailInputValidation(emailEl, 'authRegEmailFeedback');
    }
    return;
  }

  if (btn) { btn.disabled = true; btn.textContent = 'Creating account...'; }
  if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }

  const res = await clientAuth.register(name, org, email, password);
  if (btn) { btn.disabled = false; btn.textContent = 'Create Researcher Account'; }

  if (res.success) {
    closeAuthModal();
    showToast(`Account created. Welcome ${res.user.full_name} (5 runs allocated today).`);
    if (clientAuth.pendingAction === 'feedback') {
      clientAuth.pendingAction = null;
      openFeedbackModal();
    } else if (clientAuth.pendingAction === 'discovery') {
      clientAuth.pendingAction = null;
      runDiscovery();
    }
  } else {
    if (errEl) {
      errEl.textContent = res.message || 'Registration failed.';
      errEl.classList.remove('hidden');
    }
  }
}

export function handleLogout() {
  clientAuth.logout();
}

export function openQuotaModal() {
  const modal = document.getElementById('quotaExhaustedModal');
  if (!modal) return;
  openModalDialog(modal);
  const quota = clientAuth.getQuota();
  const countEl = document.getElementById('quotaModalCountdown');
  if (countEl) countEl.textContent = quota.countdown;
}

export function closeQuotaModal() {
  closeModalDialog(document.getElementById('quotaExhaustedModal'));
}

export function openFeedbackModal() {
  if (!clientAuth.isLoggedIn() && !window.isOwner) {
    clientAuth.pendingAction = 'feedback';
    openAuthModal('Please sign in or register to submit scientific feedback.');
    return;
  }

  const modal = document.getElementById('feedbackModal');
  if (!modal) return;
  openModalDialog(modal);

  const user = clientAuth.getCurrentUser();
  const idEl = document.getElementById('feedbackUserIdentity');
  if (idEl) {
    idEl.textContent = user ? `${user.email} (${user.organization || 'Independent'})` : 'Local Owner Session';
  }

  const targetSelect = document.getElementById('targetSelect');
  const currentTarget = targetSelect ? targetSelect.value : 'KRAS G12D';
  const targetEl = document.getElementById('feedbackTargetComplex');
  if (targetEl) {
    targetEl.value = `${currentTarget} (Active Exploration Complex)`;
  }

  renderFeedbackHistory();
}

export function closeFeedbackModal() {
  closeModalDialog(document.getElementById('feedbackModal'));
}

export function renderFeedbackHistory() {
  const container = document.getElementById('feedbackHistoryContainer');
  const listEl = document.getElementById('feedbackHistoryList');
  if (!container || !listEl) return;

  const history = clientAuth.getLocalFeedback();
  if (history.length === 0) {
    container.classList.add('hidden');
    return;
  }

  container.classList.remove('hidden');
  listEl.innerHTML = history.slice(0, 5).map(item => `
    <div class="p-2 rounded bg-black/40 border border-surface-border text-[11px] space-y-1">
      <div class="flex items-center justify-between">
        <span class="text-cyan-300 font-bold">${escapeHtml(item.category)}</span>
        <span class="text-amber-300 font-bold">${escapeHtml(item.rating)}/5</span>
      </div>
      <p class="text-gray-300 leading-snug break-words">${escapeHtml(item.comments)}</p>
      <div class="text-[9px] text-gray-500">${new Date(item.timestamp * 1000).toLocaleString()} · ${escapeHtml(item.target_name)}</div>
    </div>
  `).join('');
}

export async function handleFeedbackSubmit(event) {
  if (event) event.preventDefault();
  const categoryEl = document.getElementById('feedbackCategory');
  const ratingEl = document.getElementById('feedbackRating');
  const commentsEl = document.getElementById('feedbackComments');
  const errEl = document.getElementById('feedbackFormError');
  const btn = document.getElementById('feedbackSubmitBtn');
  const targetSelect = document.getElementById('targetSelect');

  const category = categoryEl ? categoryEl.value : 'General';
  const rating = ratingEl ? parseInt(ratingEl.value, 10) : 5;
  const comments = commentsEl ? commentsEl.value.trim() : '';
  const target_name = targetSelect ? targetSelect.value : 'KRAS G12D';

  if (!comments) {
    if (errEl) {
      errEl.textContent = 'Please enter your feedback comments before submitting.';
      errEl.classList.remove('hidden');
    }
    return;
  }

  if (btn) { btn.disabled = true; btn.textContent = 'Submitting feedback...'; }
  if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }

  const res = await clientAuth.submitFeedback({
    category,
    rating,
    comments,
    target_name
  });

  if (btn) { btn.disabled = false; btn.textContent = 'Submit Scientific Feedback'; }

  if (res.success) {
    if (commentsEl) commentsEl.value = '';
    closeFeedbackModal();
    showToast('Thank you. Your scientific feedback has been recorded.');
  } else {
    if (errEl) {
      errEl.textContent = res.message || 'Submission failed.';
      errEl.classList.remove('hidden');
    }
  }
}

export function openInstallModal() {
  const modal = document.getElementById('installModal');
  if (modal) {
    const liveStrip = document.getElementById('liveInstallerButtons');
    if (liveStrip) {
      liveStrip.classList.toggle('hidden', !state.isBackendAvailable);
    }
    openModalDialog(modal);
  }
}

export function closeInstallModal() {
  closeModalDialog(document.getElementById('installModal'));
}

export function closeModalOnBackdrop(e) {
  if (e.target === document.getElementById('installModal')) closeInstallModal();
}

export async function openBenchmarkModal() {
  const modal = document.getElementById('benchmarkModal');
  if (modal) {
    openModalDialog(modal);
  }
  await runLiveBenchmark();
}

export function closeBenchmarkModal(e) {
  if (e.target && e.target.id === 'benchmarkModal') {
    closeBenchmarkModalDirect();
  }
}

export function closeBenchmarkModalDirect() {
  closeModalDialog(document.getElementById('benchmarkModal'));
}

export function openRobotModal() {
  const modal = document.getElementById('robotProtocolModal');
  if (modal) {
    const targetSelect = document.getElementById('targetSelect');
    const selTarget = targetSelect?.value || '7RPZ';
    const preset = TARGETS[selTarget] || null;
    const fallbackId = preset ? `${(preset.ligandName || 'LEAD').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 11)}-SIM-01` : 'LEAD-SIM-01';
    const fallbackSmiles = preset?.referenceSmiles || 'CC(=O)Nc1ccc(O)cc1';
    const lead = state.currentSelectedLead || (state.currentLeads && state.currentLeads[0]) || { id: fallbackId, smiles: fallbackSmiles };
    const expectedKey = `${state.runId || 'idle'}:${state.selectedLeadId || lead.id}:${state.leadRevision || 0}`;

    if (!state.currentOt2Code || state.currentOt2Key !== expectedKey) {
      const ctx = buildExportContext();
      state.currentOt2Key = expectedKey;
      state.currentOt2Code = buildStaticOt2Script(ctx);
      const codeEl = document.getElementById('ot2CodeContent');
      if (codeEl) codeEl.textContent = state.currentOt2Code;
      const leadEl = document.getElementById('robotModalLeadId');
      if (leadEl) leadEl.textContent = lead.id;
      const stepEl = document.getElementById('robotModalSteps');
      if (stepEl) stepEl.textContent = `${ctx.retrosynthesis?.num_steps || 2} Steps (${ctx.retrosynthesis?.feasibility || 'Heuristic BRICS / Literature Precedent'})`;
    }
    openModalDialog(modal);
  }
}

export function closeRobotModal() {
  closeModalDialog(document.getElementById('robotProtocolModal'));
}

export function openResistanceModal() {
  openModalDialog(document.getElementById('resistanceModal'));
}

export function closeResistanceModal() {
  closeModalDialog(document.getElementById('resistanceModal'));
}

export function openStaticDemoModal() {
  openModalDialog(document.getElementById('staticDemoModal'));
}

export function closeStaticDemoModal() {
  closeModalDialog(document.getElementById('staticDemoModal'));
}

export function closeAllModals() {
  closeOwnerModal();
  closeAuthModal();
  closeQuotaModal();
  closeFeedbackModal();
  closeInstallModal();
  closeBenchmarkModalDirect();
  closeRobotModal();
  closeResistanceModal();
  closeStaticDemoModal();
  closeRawReceiptModal();
  close3DModalDirect();
  closeModalDialog(document.getElementById('tourCardModal'));
}
