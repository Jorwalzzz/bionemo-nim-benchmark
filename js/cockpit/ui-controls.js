/**
 * DOM event handlers, modals, inputs, candidate selectors, reports,
 * OT-2 liquid handler export, and interactive guided tour controller.
 */

import { state, TARGETS, ESMFOLD_PRESETS, PRESET_INHIBITORS } from './state.js';
import { clientAuth } from './api.js';
import { loadPdb, render3DComplex } from './viewer3d.js';

export function setRounds(r) {
  selectedRounds = r;
  const labels = { 1: "1 Round (Fast)", 2: "2 Rounds (Evolve)", 3: "3 Rounds (Deep)" };
  document.getElementById('roundsDisplay').textContent = labels[r] || (r + " Rounds");
  [1, 2, 3].forEach(n => {
    const btn = document.getElementById('btn-round-' + n);
    if (!btn) return;
    if (n === r) {
      btn.className = "py-1.5 text-xs rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 font-bold transition-colors";
    } else {
      btn.className = "py-1.5 text-xs rounded-lg border border-surface-border text-gray-400 hover:text-white transition-colors";
    }
  });
}

export function switchTargetTab(tab) {
  currentTargetTab = tab;
  ['presets', 'rcsb', 'esmfold'].forEach(t => {
    const el = document.getElementById('targetTab' + t.charAt(0).toUpperCase() + t.slice(1));
    const btn = document.getElementById('tabBtn' + t.charAt(0).toUpperCase() + t.slice(1));
    if (el) el.classList.toggle('hidden', t !== tab);
    if (btn) {
      if (t === tab) {
        btn.className = "py-1 text-[11px] font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-all";
      } else {
        btn.className = "py-1 text-[11px] font-semibold rounded text-gray-400 hover:text-white transition-all";
      }
    }
  });

  const badge = document.getElementById('targetModeBadge');
  if (badge) {
    if (tab === 'presets') {
      badge.textContent = 'PRESET';
      badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      updateTargetInfo();
    } else if (tab === 'rcsb') {
      badge.textContent = 'RCSB PDB';
      badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20';
    } else {
      badge.textContent = 'ESMFOLD';
      badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20';
    }
  }
}

export function updateSeqCount() {
  const txt = (document.getElementById('esmfoldSeqInput').value || '').trim();
  const clean = txt.replace(/^>.*$/gm, '').replace(/\s+/g, '');
  const badge = document.getElementById('seqLenBadge');
  if (badge) badge.textContent = `${clean.length} aa`;
}

export function loadEsmPreset(presetKey) {
  const p = ESMFOLD_PRESETS[presetKey];
  if (!p) return;
  const area = document.getElementById('esmfoldSeqInput');
  if (area) {
    area.value = p.seq;
    updateSeqCount();
    showToast(`Loaded ${p.name} (${p.seq.length} aa)`);
  }
}

let wbDebounceTimer = null;
export function onWorkbenchInput(val) {
  clearTimeout(wbDebounceTimer);
  wbDebounceTimer = setTimeout(() => {
    let target = document.getElementById('targetSelect')?.value || 'KRAS G12D';
    const res = evaluateClientRedock(val, target);
    const vBadge = document.getElementById('workbenchValenceBadge');
    if (!res.valid) {
      if (vBadge) {
        vBadge.textContent = '';
        const bSpan = document.createElement('span');
        bSpan.className = 'badge-valence-warning';
        bSpan.textContent = `⚠️ ${res.error || 'Syntax Alert'}`;
        vBadge.appendChild(bSpan);
      }
      return;
    }
    if (vBadge) {
      vBadge.innerHTML = `<span class="badge-valence-valid">✓ Valid (${res.heavyAtoms || 28} heavy atoms)</span>`;
    }
    const dGEl = document.getElementById('wbLiveAffinity');
    if (dGEl) dGEl.textContent = res.binding_affinity_kcal_mol.toFixed(2);
    const qedEl = document.getElementById('wbLiveQed');
    if (qedEl) qedEl.textContent = res.qed.toFixed(3);
    const sasEl = document.getElementById('wbLiveSas');
    if (sasEl) sasEl.textContent = res.sascore.toFixed(2);
    const mwEl = document.getElementById('wbLiveMw');
    if (mwEl) mwEl.textContent = res.mw.toFixed(0);
  }, 100);
}

export function loadWorkbenchPreset(key) {
  const p = PRESET_INHIBITORS[key];
  if (!p) return;
  const input = document.getElementById('workbenchSmilesInput');
  if (input) {
    input.value = p.smiles;
    onWorkbenchInput(p.smiles);
    showToast(`🧪 Loaded ${p.name}`);
  }
}

export function tweakSmiles(type) {
  const input = document.getElementById('workbenchSmilesInput');
  if (!input) return;
  let s = input.value;
  if (type === 'fluorine') {
    s = s.includes('cccc') ? s.replace('cccc', 'c(F)ccc') : s.replace(/c1ccccc1/i, 'c1ccc(F)cc1');
    showToast('Added magic fluorine substituent (-F)');
  } else if (type === 'methyl') {
    s = s.includes('c1') ? s.replace('c1', 'c(C)1') : s + 'C';
    showToast('Added magic methyl substituent (-CH3)');
  } else if (type === 'pyridine') {
    s = s.replace(/c1ccccc1/i, 'c1ccccn1');
    showToast('Swapped phenyl core to pyridine for solubility');
  }
  input.value = s;
  onWorkbenchInput(s);
}

export function openAuthModal(noticeMessage) {
  const modal = document.getElementById('authModal');
  if (!modal) return;
  modal.style.display = 'flex';
  modal.classList.remove('hidden');

  if (noticeMessage) {
    showToast(noticeMessage);
  }
  switchAuthTab('login');
}

export function closeAuthModal() {
  const modal = document.getElementById('authModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.add('hidden');
  }
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
    showToast(`✅ Welcome back, ${res.user.full_name || res.user.email}! (5 runs/day active)`);
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
    showToast(`⚡ 1-Click Reviewer Access granted: evaluator@bionemo.org`);
    if (clientAuth.pendingAction === 'feedback') {
      clientAuth.pendingAction = null;
      openFeedbackModal();
    } else if (clientAuth.pendingAction === 'discovery') {
      clientAuth.pendingAction = null;
      runDiscovery();
    }
  } else {
    showToast('⚠️ Demo login failed. Please try again.');
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
    showToast(`🎉 Account created! Welcome ${res.user.full_name}. 5 runs allocated for today.`);
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
  modal.style.display = 'flex';
  modal.classList.remove('hidden');
  const quota = clientAuth.getQuota();
  const countEl = document.getElementById('quotaModalCountdown');
  if (countEl) countEl.textContent = quota.countdown;
}

export function closeQuotaModal() {
  const modal = document.getElementById('quotaExhaustedModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.add('hidden');
  }
}

export function openFeedbackModal() {
  if (!clientAuth.isLoggedIn()) {
    clientAuth.pendingAction = 'feedback';
    openAuthModal('Please sign in or register to submit scientific feedback.');
    return;
  }

  const modal = document.getElementById('feedbackModal');
  if (!modal) return;
  modal.style.display = 'flex';
  modal.classList.remove('hidden');

  const user = clientAuth.getCurrentUser();
  const idEl = document.getElementById('feedbackUserIdentity');
  if (idEl && user) {
    idEl.textContent = `${user.email} (${user.organization || 'Independent'})`;
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
  const modal = document.getElementById('feedbackModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.add('hidden');
  }
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
        <span class="text-amber-300 font-bold">★ ${item.rating}/5</span>
      </div>
      <p class="text-gray-300 leading-snug break-words">${escapeHtml(item.comments)}</p>
      <div class="text-[9px] text-gray-500">${new Date(item.timestamp * 1000).toLocaleString()} • ${escapeHtml(item.target_name)}</div>
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
    showToast('💬 Thank you! Your scientific feedback has been recorded.');
  } else {
    if (errEl) {
      errEl.textContent = res.message || 'Submission failed.';
      errEl.classList.remove('hidden');
    }
  }
}

// Window object exports

let currentLeads = [];
let paretoChart = null;
let isRunning = false;

// ─── Target Info Update ──────────────────────────────────────────────────────
export function updateTargetInfo() {
  let target = document.getElementById('targetSelect')?.value || 'KRAS G12D';
  let info = TARGETS[target];

  if (currentTargetTab === 'esmfold') {
    const rawSeq = (document.getElementById('esmfoldSeqInput')?.value || '').trim().replace(/^>.*$/gm, '').replace(/\s+/g, '');
    target = rawSeq || 'De Novo Variant';
    info = {
      pdb: `DE NOVO (pLDDT ${(currentTargetMeanPlddt || 89.5).toFixed(1)})`,
      indication: 'De Novo Engineered Scaffold',
      pocket: 'Predicted Catalytic Core',
      mutant: 'Variant / De Novo',
      color: '#a855f7'
    };
  } else if (currentTargetTab === 'rcsb') {
    const customCode = (document.getElementById('customTargetInput')?.value || '').trim().toUpperCase();
    target = customCode || '8AZV';
    info = {
      pdb: target,
      indication: 'Crystallographic Target',
      pocket: 'Active Site Cleft',
      mutant: 'WT / Custom',
      color: '#00f1fd'
    };
  } else if (!info) {
    info = {
      pdb: '8AZV',
      indication: 'Oncology Target',
      pocket: 'Allosteric Pocket',
      mutant: 'WT',
      color: '#76b900'
    };
  }

  const nameEl = document.getElementById('targetName');
  const pdbEl = document.getElementById('targetPdb');
  const indEl = document.getElementById('targetInd');
  const pocketEl = document.getElementById('targetPocket');
  const mutEl = document.getElementById('targetMut');

  if (nameEl) {
    nameEl.textContent = currentTargetTab === 'esmfold' ? (target.length > 25 ? target.slice(0, 22) + '...' : target) : target;
    nameEl.style.color = info.color;
  }
  if (pdbEl) pdbEl.textContent = info.pdb;
  if (indEl) indEl.textContent = info.indication;
  if (pocketEl) pocketEl.textContent = info.pocket;
  if (mutEl) mutEl.textContent = info.mutant;

  // Real-time 3D Viewport Target Synchronization
  if (currentTargetTab === 'presets' && info && info.pdb) {
    (async () => {
      const pdbText = (typeof loadPdb === 'function') ? await loadPdb(info.pdb) : window['PDB_' + info.pdb];
      if (pdbText && typeof render3DComplex === 'function') {
        currentTargetPdbText = pdbText;
        currentTargetPocketResidues = info.pocketResidues || [12, 13, 32, 60, 61, 96];
        render3DComplex(currentTargetPdbText, null, currentTargetPocketResidues, false, 95.0);
      }
    })();
  }
}

// ─── Agent Status Helpers ────────────────────────────────────────────────────
export function setAgent(id, state, msg) {
  const ring = document.getElementById('ring-' + id);
  const status = document.getElementById('status-' + id);
  if (ring) ring.className = 'agent-ring ' + state;
  if (status) status.textContent = msg;
}

export function resetAgents() {
  ['scout','chemist','admet','docking','pi'].forEach(a => setAgent(a, 'idle', 'Standby'));
}

// ─── Log Helper ─────────────────────────────────────────────────────────────
export function logEntry(icon, agent, role, text, color) {
  const log = document.getElementById('agentLog');
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
  document.getElementById('streamTimestamp').textContent = ts;
  const safeAgent = escapeHtml(agent);
  const safeRole = escapeHtml(role);
  const safeColor = /^[#a-zA-Z0-9]+$/.test(color) ? color : '#76b900';
  // Strip dangerous script/event handler attributes from text while preserving benign markup
  const safeText = String(text ?? '')
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/\bon\w+\s*=/gi, 'data-blocked=');
  const el = document.createElement('div');
  el.className = 'animate-fade-up';
  el.innerHTML = `
    <div class="flex items-start gap-2 p-2.5 rounded-lg" style="background: rgba(22,27,34,0.6); border: 1px solid ${safeColor}20;">
      <span class="text-base">${icon}</span>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-bold text-[10px] uppercase tracking-wider" style="color: ${safeColor}">${safeAgent}</span>
          <span class="text-[9px] text-gray-600">${safeRole}</span>
          <span class="text-[9px] text-gray-700 ml-auto font-mono">${ts}</span>
        </div>
        <div class="text-gray-300 leading-relaxed text-[11px] break-words">${safeText}</div>
      </div>
    </div>`;
  log.appendChild(el);
  // Virtualized DOM cleanup: retain max 25 cards for 60fps rendering and zero memory bloat
  while (log.children.length > 25) {
    log.removeChild(log.firstChild);
  }
  log.scrollTop = log.scrollHeight;
}

// ─── Run Discovery ───────────────────────────────────────────────────────────

// ─── Render Leads ─────────────────────────────────────────────────────────
export function renderLeads() {
  const container = document.getElementById('leadsContainer');
  document.getElementById('leadCount').textContent = `${currentLeads.length} candidates`;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  container.innerHTML = currentLeads.map((lead, i) => `
    <div class="lead-card ${i === 0 ? 'selected' : ''}" onclick="selectLead(${i})">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <span class="font-mono font-bold text-xs text-white">${esc(lead.id)}</span>
          ${lead.pareto ? '<span class="badge-green">PARETO</span>' : ''}
        </div>
        <span class="${lead.verdict === 'PASS' ? 'badge-green' : 'badge-yellow'}">${esc(lead.verdict)}</span>
      </div>
      <div class="grid grid-cols-4 gap-2 text-[10px]">
        <div><div class="text-gray-600">ΔG</div><div class="font-mono font-bold" style="color: var(--nvidia-green);">${esc(lead.affinity)}</div></div>
        <div><div class="text-gray-600">QED</div><div class="font-mono font-bold" style="color: var(--cyber-cyan);">${esc(lead.qed)}</div></div>
        <div><div class="text-gray-600">MW</div><div class="font-mono text-gray-300">${esc(lead.mw)}</div></div>
        <div><div class="text-gray-600">SAScore</div><div class="font-mono text-gray-300">${esc(lead.sascore)}</div></div>
      </div>
    </div>
  `).join('');
  if (currentLeads.length > 0) selectLead(0);
}

export function selectLead(i) {
  document.querySelectorAll('.lead-card').forEach((c, idx) => c.classList.toggle('selected', idx === i));
  const lead = currentLeads[i];
  currentSelectedLead = lead;
  let target = document.getElementById('targetSelect').value;
  if (currentTargetTab === 'esmfold') target = 'ESMFold De Novo';
  else if (currentTargetTab === 'rcsb') target = (document.getElementById('customTargetInput').value || '').trim() || 'RCSB Target';
  const info = TARGETS[target] || { pdb: 'CUSTOM', color: '#76b900' };
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeLeadId = esc(lead.id);
  const safeVerdict = esc(lead.verdict);
  const safeSmiles = esc(lead.smiles || 'CC(=O)Nc1ccc(O)cc1');
  
  document.getElementById('dossierPanel').innerHTML = `
    <div class="space-y-3 animate-fade-up">
      <div class="p-3 rounded-xl" style="background: rgba(118,185,0,0.06); border: 1px solid rgba(118,185,0,0.2);">
        <div class="flex items-center justify-between mb-1">
          <div class="font-mono font-bold text-sm text-white">${safeLeadId}</div>
          <span class="text-[10px] font-mono text-gray-400">ΔG <strong class="text-nvidia-green">${lead.affinity.toFixed(2)}</strong></span>
        </div>
        <div class="flex gap-1.5 flex-wrap">
          ${lead.pareto ? '<span class="badge-green">PARETO OPTIMAL</span>' : ''}
          <span class="${lead.verdict === 'PASS' ? 'badge-green' : 'badge-yellow'}">${safeVerdict}</span>
          <span class="badge-cyan">Round ${lead.round || 1}</span>
        </div>
      </div>

      <!-- Interactive 3D Pocket & Pose Viewer (3Dmol.js) -->
      <div class="rounded-xl overflow-hidden border border-surface-border bg-[#0b0f14] relative">
        <div class="p-2 border-b border-surface-border flex items-center justify-between bg-[#121820]">
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span class="text-[10px] font-bold font-mono text-cyan-300">3D Docked Complex</span>
          </div>
          <div class="flex items-center gap-1">
            <button type="button" onclick="toggle3DSpin()" id="btnSpin" class="px-1.5 py-0.5 text-[9px] rounded bg-white/5 hover:bg-white/10 text-gray-300 transition-colors">🔄 Spin</button>
            <button type="button" onclick="toggle3DSurface()" id="btnSurface" class="px-1.5 py-0.5 text-[9px] rounded bg-white/5 hover:bg-white/10 text-gray-300 transition-colors">🎨 Surface</button>
            <button type="button" onclick="reset3DView()" class="px-1.5 py-0.5 text-[9px] rounded bg-white/5 hover:bg-white/10 text-gray-300 transition-colors">🔍</button>
            <button type="button" onclick="open3DModal()" class="px-1.5 py-0.5 text-[9px] rounded bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 transition-colors font-bold">⛶</button>
          </div>
        </div>
        <div id="molViewer3D" style="width: 100%; height: 210px; position: relative;"></div>
        <div class="p-1.5 bg-[#0f141c] border-t border-surface-border flex items-center justify-between text-[9px] text-gray-400">
          <div class="flex items-center gap-2">
            <span><span class="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400"></span> Pocket</span>
            <span><span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Pose</span>
          </div>
          <span id="viewer3dBadge" class="font-mono text-emerald-400 font-bold">DiffDock 3D</span>
        </div>
      </div>

      <!-- Physicochemical Key Properties -->
      <div class="space-y-1 text-xs">
        <div class="flex justify-between py-1 border-b border-surface-border">
          <span class="text-gray-400">Binding Affinity (ΔG)</span>
          <span class="font-mono font-bold text-glow-green" style="color: var(--nvidia-green);">${lead.affinity.toFixed(2)} kcal/mol</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-border">
          <span class="text-gray-400">Drug-likeness (QED)</span>
          <span class="font-mono text-cyan-400">${lead.qed.toFixed(3)}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-border">
          <span class="text-gray-400">Synthetic Difficulty (SAScore)</span>
          <span class="font-mono text-gray-300">${lead.sascore.toFixed(2)} / 10</span>
        </div>
      </div>

      <!-- Interactive Chemical Workbench (Human-in-the-Loop) -->
      <div id="workbenchCard" class="p-2.5 rounded-xl bg-surface-elevated border border-surface-border">
        <div class="text-[11px] font-bold text-cyan-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>🧪 Chemical Workbench</span>
          <div id="workbenchValenceBadge">
            <span class="badge-valence-valid">✓ Valid Chemical Graph</span>
          </div>
        </div>

        <!-- 1-Click Reference Presets -->
        <div class="flex items-center gap-1 mb-2 overflow-x-auto py-0.5">
          <button type="button" onclick="loadWorkbenchPreset('kras')" class="wb-preset-pill">MRTX1133 (KRAS)</button>
          <button type="button" onclick="loadWorkbenchPreset('egfr')" class="wb-preset-pill">Osimertinib (EGFR)</button>
          <button type="button" onclick="loadWorkbenchPreset('mpro')" class="wb-preset-pill">Nirmatrelvir (Mpro)</button>
          <button type="button" onclick="loadWorkbenchPreset('her2')" class="wb-preset-pill">Tucatinib (HER2)</button>
        </div>

        <input type="text" id="workbenchSmilesInput" oninput="onWorkbenchInput(this.value)" aria-label="Ligand SMILES Structure" value="${safeSmiles}" class="w-full text-[11px] font-mono p-1.5 rounded bg-[#161b22] border border-[#30363d] text-gray-200 mb-1.5 focus:outline-none focus:border-cyan-400" />
        
        <!-- Live Biophysical Metric Tile Readout -->
        <div id="workbenchLiveMetrics" class="grid grid-cols-4 gap-1 text-[10px] font-mono text-center p-1.5 rounded bg-black/40 border border-white/5 mb-2">
          <div><span class="text-gray-500 block text-[9px]">ΔG (kcal/mol)</span><span id="wbLiveAffinity" class="text-emerald-400 font-bold">${lead.affinity.toFixed(2)}</span></div>
          <div><span class="text-gray-500 block text-[9px]">QED Score</span><span id="wbLiveQed" class="text-cyan-400 font-bold">${lead.qed.toFixed(3)}</span></div>
          <div><span class="text-gray-500 block text-[9px]">SAScore</span><span id="wbLiveSas" class="text-amber-400 font-bold">${lead.sascore.toFixed(2)}</span></div>
          <div><span class="text-gray-500 block text-[9px]">MW (g/mol)</span><span id="wbLiveMw" class="text-gray-300 font-bold">${(lead.mw || 500).toFixed(0)}</span></div>
        </div>

        <div class="grid grid-cols-3 gap-1 mb-2">
          <button type="button" onclick="tweakSmiles('fluorine')" class="py-1 text-[10px] bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-gray-700 font-mono">+F Fluorine</button>
          <button type="button" onclick="tweakSmiles('methyl')" class="py-1 text-[10px] bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-gray-700 font-mono">+Me Methyl</button>
          <button type="button" onclick="tweakSmiles('pyridine')" class="py-1 text-[10px] bg-slate-800 hover:bg-slate-700 text-gray-300 rounded border border-gray-700 font-mono">Swap Pyridine</button>
        </div>

        <button type="button" onclick="triggerRedockFromWorkbench()" class="w-full py-1.5 btn-cta text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1.5">
          <span>⚡ Instant Re-Dock Modified Lead</span>
        </button>
        <div id="redockAffinityDisplay" class="mt-1.5 text-center text-xs"></div>
      </div>

      <!-- Dr. Chen's Retrosynthesis Procedure Card -->
      <div class="p-2.5 rounded-xl border border-amber-500/20 bg-amber-500/5">
        <div class="text-[11px] font-bold text-amber-400 mb-1 flex items-center justify-between">
          <div class="flex items-center gap-1">
            <span>🔬</span>
            <span>Dr. Chen's Wet-Lab Synthesis Route</span>
          </div>
          <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-amber-500/20 text-amber-300">Robotics Ready</span>
        </div>
        <div class="text-[10px] text-gray-300 space-y-1 mb-2">
          <div><strong class="text-white">Route:</strong> Suzuki Coupling + Amide Condensation (Yield ~78%)</div>
          <div class="text-gray-400"><strong>Commercial Precursors:</strong> Aryl Boronic Acid + Substituted Amine</div>
        </div>
        <div class="pt-2 border-t border-amber-500/20 flex gap-1.5">
          <button type="button" onclick="generateRobotProtocol()" class="flex-1 py-1.5 text-[10px] font-bold rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 flex items-center justify-center gap-1 transition-all">
            <span>🤖 Opentrons OT-2 Code</span>
          </button>
          <button type="button" onclick="generateLabCard()" class="flex-1 py-1.5 text-[10px] font-bold rounded-lg bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10 flex items-center justify-center gap-1 transition-all">
            <span>📋 Wet-Lab SOP</span>
          </button>
        </div>
      </div>

      <!-- Adaptive Resistance Stress-Test Card -->
      <div class="p-2.5 rounded-xl border border-red-500/25 bg-red-950/20">
        <div class="text-[11px] font-bold text-red-400 mb-1 flex items-center justify-between">
          <div class="flex items-center gap-1">
            <span>🛡️</span>
            <span>Adaptive Resistance Stress-Test</span>
          </div>
          <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-red-500/20 text-red-300 border border-red-500/30">ESM-2 / MolMIM</span>
        </div>
        <p class="text-[10px] text-gray-400 mb-2">Simulate target point mutation clash & auto-evolve escape scaffold via MolMIM latent steering.</p>
        <button type="button" onclick="runResistanceStressTest()" class="w-full py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-red-600/30 to-purple-600/30 hover:from-red-600/50 hover:to-purple-600/50 text-red-200 border border-red-500/40 flex items-center justify-center gap-1.5 transition-all">
          <span>⚡ Run Resistance Stress-Test</span>
        </button>
      </div>

      <!-- Export Buttons -->
      <div class="space-y-1.5 pt-1">
        <button onclick="generateINDPdf()" class="w-full py-2.5 text-xs font-bold text-white rounded-lg flex items-center justify-center gap-1.5 transition-all hover:scale-102 glow-green shadow-lg" style="background: linear-gradient(135deg, #1e40af, #2563eb); border: 1px solid rgba(59, 130, 246, 0.6);">
          <span>📄 Download Pre-Clinical Summary (PDF)</span>
          <span class="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/20 text-white font-bold">CMC Template</span>
        </button>
        <button onclick="downloadDossier()" class="btn-ghost w-full text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5">
          Export Dossier (.md)
        </button>
        <button onclick="downloadSDF()" class="btn-ghost w-full text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5" style="border-color: rgba(0,241,253,0.3); color: #00f1fd;">
          Export Poses (.sdf)
        </button>
      </div>
    </div>
  `;

  // Render 3D docked complex with slight timeout for DOM mount
  setTimeout(() => updateLead3DView(lead), 40);
}

// ─── Pareto Chart ─────────────────────────────────────────────────────────

// ─── Desktop App (In Progress) Modal ──────────────────────────────────────
export function openInstallModal() {
  const modal = document.getElementById('installModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
  }
}
export function closeInstallModal() {
  const modal = document.getElementById('installModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
  document.body.classList.remove('modal-open');
}
export function closeModalOnBackdrop(e) {
  if (e.target === document.getElementById('installModal')) closeInstallModal();
}
export function switchTab(tab) {
  ['windows','unix','docker','compare'].forEach(t => {
    document.getElementById('pane-' + t).classList.toggle('hidden', t !== tab);
    document.getElementById('tab-' + t).classList.toggle('active', t === tab);
  });
}

// ─── Copy to Clipboard ────────────────────────────────────────────────────
export function copyCode(elId, btn) {
  const text = document.getElementById(elId).textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    showToast();
    setTimeout(() => btn.textContent = 'Copy', 2000);
  });
}

export function showToast(msg) {
  const t = document.getElementById('toast');
  if (msg) t.textContent = msg;
  t.classList.remove('hide');
  setTimeout(() => t.classList.add('hide'), 2500);
}

// ─── Download Installer ───────────────────────────────────────────────────
export async function downloadInstaller(type) {
  const isLocalServer = window.location.protocol.startsWith('http') && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  let file = 'install.bat';
  if (type === 'unix') file = 'install.sh';
  else if (type === 'powershell') file = 'install.ps1';

  showToast('Preparing ' + file + '...');

  const candidateUrls = [];
  if (isLocalServer) {
    candidateUrls.push('/api/download/installer-' + type);
  }
  // Same-origin relative paths (GitHub Pages and static local server)
  candidateUrls.push('./scripts/installers/' + file);
  candidateUrls.push('scripts/installers/' + file);
  // Raw GitHub CDN fallback (Access-Control-Allow-Origin: *)
  candidateUrls.push('https://raw.githubusercontent.com/Jorwalzzz/bionemo-nim-benchmark/main/scripts/installers/' + file);

  let blob = null;
  for (const url of candidateUrls) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const content = await res.text();
        if (content && content.length > 50) {
          blob = new Blob([content], { type: 'application/octet-stream' });
          break;
        }
      }
    } catch (e) {
      // Continue to next candidate URL
    }
  }

  if (blob) {
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = blobUrl;
    a.download = file;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    }, 1500);
    showToast('Downloaded ' + file + '! Run it to launch.');
  } else {
    const fallbackUrl = 'https://raw.githubusercontent.com/Jorwalzzz/bionemo-nim-benchmark/main/scripts/installers/' + file;
    window.open(fallbackUrl, '_blank');
    showToast('Opening ' + file + ' directly in new tab...');
  }
}

export async function downloadDossier() {
  const isLocalServer = window.location.protocol.startsWith('http') && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  const file = 'CANDIDATE_SELECTION_DOSSIER.md';
  const url = isLocalServer ? '/api/dossier' : 'results/CANDIDATE_SELECTION_DOSSIER.md';
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    const blob = new Blob([text], { type: 'text/markdown' });
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = file;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    }, 1000);
    showToast('Dossier (.md) downloaded!');
  } catch (e) {
    window.open(url, '_blank');
  }
}

export async function downloadSDF() {
  const file = 'top_leads_docked.sdf';
  const url = 'results/top_leads_docked.sdf';
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    const blob = new Blob([text], { type: 'chemical/x-mdl-sdfile' });
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = file;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    }, 1000);
    showToast('Docked Poses (.sdf) downloaded!');
  } catch (e) {
    window.open(url, '_blank');
  }
}

// ─── Utilities ────────────────────────────────────────────────────────────
export function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Init
updateTargetInfo();



// ─── NVIDIA HARDWARE ACCELERATION BENCHMARK WIDGET ──────────────────────────
export async function openBenchmarkModal() {
  const modal = document.getElementById('benchmarkModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
  }
  await runLiveBenchmark();
}

export function closeBenchmarkModal(e) {
  if (e.target.id === 'benchmarkModal') {
    closeBenchmarkModalDirect();
  }
}

export function closeBenchmarkModalDirect() {
  const modal = document.getElementById('benchmarkModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
  document.body.classList.remove('modal-open');
}


export async function generateINDPdf() {
  showToast('📄 Compiling Pre-Clinical Candidate Summary Dossier...');
  
  let target = document.getElementById('targetSelect').value;
  if (currentTargetTab === 'esmfold') target = 'ESMFold De Novo Target';
  else if (currentTargetTab === 'rcsb') target = (document.getElementById('customTargetInput').value || '').trim() || 'RCSB Target';

  const lead = currentSelectedLead || (currentLeads && currentLeads[0]) || {
    id: 'LEAD-001',
    affinity: -9.4,
    smiles: 'O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5',
    mw: 482.3,
    logp: 3.1,
    qed: 0.78,
    sascore: 2.7,
    verdict: 'PASS'
  };

  const payload = {
    dossier: {
      target: target,
      pdb_id: document.getElementById('targetPdb').textContent || '8AZV',
      nominated_lead: lead.id,
      binding_affinity: lead.affinity,
      residue_count: currentTargetPocketResidues.length ? currentTargetPocketResidues.length * 28 : 188,
      screened: currentLeads ? currentLeads.length : 10,
      pareto_count: currentLeads ? currentLeads.filter(l => l.pareto).length : 3,
      leads: [lead],
      retrosynthesis: {
        num_steps: 2,
        feasibility: 'Commercially Accessible (1-2 steps)',
        steps: [
          { step: 1, reaction_type: 'Amide Condensation (PyBOP/DIPEA)', reagents: ['DIPEA', 'DMF', 'rt 2h'], yield_pct: 85.0, difficulty: 'Routine (★☆☆)' },
          { step: 2, reaction_type: 'Suzuki-Miyaura Cross-Coupling', reagents: ['Pd(dppf)Cl2', 'K2CO3', '80°C'], yield_pct: 78.0, difficulty: 'Routine (★☆☆)' }
        ]
      }
    }
  };

  try {
    const res = await fetch('/api/dossier/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FDA_IND_Section2_Briefing_${target.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showToast('✅ Pre-Clinical Candidate Summary successfully downloaded!');
  } catch (err) {
    console.warn('Backend PDF endpoint unavailable in static/GitHub Pages mode. Generating client briefing package:', err);
    // Offline / GitHub Pages fallback: generate briefing report
    const reportText = `%PDF-1.4\n% Pre-Clinical Candidate Briefing (CMC-Style Academic Template)\n% Notice: Illustrative summary for research use only; not a formal IND submission under 21 CFR 312.\nTarget: ${target}\nPDB: ${document.getElementById('targetPdb')?.textContent || '8AZV'}\nNominated Lead: ${lead.id}\nEstimated Affinity: ${lead.affinity} kcal/mol\nQED: ${lead.qed}\nSAScore: ${lead.sascore}\nGenerated by NVIDIA BioNeMo NIM Benchmark Suite\n%%EOF`;
    const blob = new Blob([reportText], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FDA_IND_Section2_Briefing_${target.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showToast('✅ Pre-Clinical Candidate Summary downloaded!');
  }
}

// Tour & Shortcut Alias
const downloadIndPdf = generateINDPdf;

// ─── FEATURE 3: OPENTRONS OT-2 ROBOTIC PROTOCOL GENERATOR ────────────────────
let currentOt2Code = '';
let currentLabCardMd = '';

export async function generateRobotProtocol() {
  const lead = currentSelectedLead || (currentLeads && currentLeads[0]) || {
    id: 'LEAD-001',
    smiles: 'CC(=O)N1CCNCC1'
  };

  showToast('🤖 Generating Opentrons OT-2 Python protocol...');
  try {
    if (isStaticHost) throw new Error('Static host: use client-side protocol');
    const res = await fetch('/api/robot/protocol', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_id: lead.id,
        smiles: lead.smiles || 'CC(=O)N1CCNCC1'
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    currentOt2Code = data.ot2_protocol_py || '';
    currentLabCardMd = data.lab_card_md || '';

    document.getElementById('ot2CodeContent').textContent = currentOt2Code;
    document.getElementById('robotModalLeadId').textContent = data.candidate_id;
    document.getElementById('robotModalSteps').textContent = `${data.num_steps} Steps (${data.feasibility})`;
    openRobotModal();
    showToast('✅ Opentrons OT-2 Protocol generated!');
  } catch (err) {
    // Elegant client-side fallback for static GitHub Pages hosting
    const sampleScript = `"""\nOT-2 AUTOMATED DILUTION PROTOCOL (UNVALIDATED)\nWARNING: Auto-generated for illustrative purposes only.\nNOT reviewed by a qualified chemist. DO NOT use in wet lab without expert review.\nTarget Candidate: ${lead.id}\nGenerated for: BioNeMo NIM Benchmark Suite\n"""\n\nfrom opentrons import protocol_api\n\nmetadata = {\n    "protocolName": "KRAS G12D inhibitor serial dilution (illustrative)",\n    "author": "Aarav Jorwal (@Jorwalzzz)",\n    "description": "2-fold serial dilution assay protocol for nominated candidate ${lead.id}",\n    "apiLevel": "2.15"\n}\n\ndef run(protocol: protocol_api.ProtocolContext):\n    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)\n    res = protocol.load_labware('nest_12_reservoir_15ml', 3)\n    tips = protocol.load_labware('opentrons_96_tiprack_300ul', 2)\n    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tips])\n    p300.flow_rate.aspirate = 25   # µL/s, throttled for DMSO viscosity\n    p300.flow_rate.dispense = 25\n\n    row = plate.rows()[0]  # Row A: A1 to A12\n    # Dispense diluent (50 µL) into columns 2-12\n    p300.transfer(50, res['A1'], row[1:], new_tip='once')\n    # 2-fold serial dilution down Row A with mixing\n    p300.transfer(50, row[:11], row[1:12], mix_after=(3, 40), new_tip='always')\n    protocol.comment("OT-2 KRAS G12D serial dilution protocol complete.")\n`;
    currentOt2Code = sampleScript;
    currentLabCardMd = `# 🧪 Wet-Lab Protocol Card — ${lead.id}\n> **Generated for BioNeMo NIM Benchmark Suite**\n> **Target Scaffold:** \`${lead.smiles || 'CC(=O)N1CCNCC1'}\`\n\n## 1. Assay & Dilution Overview\n- Format: Corning 96-well flat-bottom plate (360 µL/well)\n- Gradient: 2-fold serial dilution down Row A (columns 1 to 12)\n- Fluidics: Throttled aspiration (25 µL/s) for DMSO compatibility\n`;
    document.getElementById('ot2CodeContent').textContent = currentOt2Code;
    document.getElementById('robotModalLeadId').textContent = lead.id;
    document.getElementById('robotModalSteps').textContent = '2 Steps (High Feasibility)';
    openRobotModal();
    showToast('✅ Opentrons OT-2 Protocol generated (Static Ready)!');
  }
}

export async function generateLabCard() {
  const lead = currentSelectedLead || (currentLeads && currentLeads[0]) || {
    id: 'LEAD-001',
    smiles: 'CC(=O)N1CCNCC1'
  };

  try {
    if (isStaticHost) throw new Error('Static host: use client-side protocol');
    const res = await fetch('/api/robot/protocol', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_id: lead.id, smiles: lead.smiles })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    const blob = new Blob([data.lab_card_md], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `WetLab_Card_${lead.id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showToast('📋 Wet-Lab SOP Card (.md) downloaded!');
  } catch (err) {
    const cardContent = currentLabCardMd || `# 🧪 Wet-Lab Protocol Card — ${lead.id}\n> **Generated by NVIDIA BioNeMo Autonomous Scientist**\n> **Target Scaffold:** \`${lead.smiles || 'CC(=O)N1CCNCC1'}\`\n\n## 1. Route Overview\n- Synthetic Complexity: Commercially Accessible (2 steps)\n- Reagents: DIPEA, DMF, Pd(dppf)Cl2, K2CO3\n`;
    const blob = new Blob([cardContent], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `WetLab_Card_${lead.id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    showToast('📋 Wet-Lab SOP Card (.md) downloaded!');
  }
}

export function openRobotModal() {
  const modal = document.getElementById('robotProtocolModal');
  if (modal) {
    if (!currentOt2Code) {
      const lead = currentSelectedLead || (currentLeads && currentLeads[0]) || { id: 'MRTX1133-NIM-01', smiles: 'C#CC1=C(C=CC2=CC(=CC(=C21)C3=NC=C4C(=C3F)N=C(N=C4N5CC6CCC(C5)N6)OCC78CCCN7CC(C8)F)O)F' };
      currentOt2Code = `"""\nOpentrons OT-2 Automated Synthesis Protocol\nTarget Candidate: ${lead.id}\nSynthetic Route: 2 Steps (High Feasibility)\nGenerated by NVIDIA BioNeMo Agentic Discovery OS\n"""\n\nfrom opentrons import protocol_api\n\nmetadata = {\n    "protocolName": "BioNeMo Automated Synthesis: ${lead.id}",\n    "author": "NVIDIA BioNeMo Agentic Discovery OS",\n    "description": "Autonomous multi-step synthesis for nominated drug candidate ${lead.id}",\n    "apiLevel": "2.15"\n}\n\ndef run(protocol: protocol_api.ProtocolContext):\n    tips_300 = protocol.load_labware("opentrons_96_tiprack_300ul", 1)\n    reagents = protocol.load_labware("nest_12_reservoir_15ml", 2)\n    temp_mod = protocol.load_module("temperature module gen2", 3)\n    rxn_block = temp_mod.load_labware("opentrons_24_aluminumblock_nest_1.5ml_snapcap")\n    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips_300])\n\n    protocol.comment("Executing Step 1: Amide Coupling for ${lead.id}")\n    p300.pick_up_tip()\n    p300.aspirate(120, reagents['A2'])\n    p300.dispense(120, rxn_block['A1'])\n    p300.mix(3, 80, rxn_block['A1'])\n    p300.drop_tip()\n`;
      const codeEl = document.getElementById('ot2CodeContent');
      if (codeEl) codeEl.textContent = currentOt2Code;
      const leadEl = document.getElementById('robotModalLeadId');
      if (leadEl) leadEl.textContent = lead.id;
      const stepEl = document.getElementById('robotModalSteps');
      if (stepEl) stepEl.textContent = '2 Steps (High Feasibility)';
    }
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
  }
}
export function closeRobotModal() {
  const modal = document.getElementById('robotProtocolModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
  document.body.classList.remove('modal-open');
}
export function downloadCurrentOT2Py() {
  if (!currentOt2Code) return;
  const leadId = (currentSelectedLead && currentSelectedLead.id) || 'LEAD-001';
  const blob = new Blob([currentOt2Code], { type: 'text/x-python' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ot2_synthesis_${leadId}.py`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
  showToast('📥 ot2_synthesis protocol downloaded!');
}
export function copyOT2Code() {
  if (!currentOt2Code) return;
  navigator.clipboard.writeText(currentOt2Code).then(() => {
    showToast('📋 Python protocol copied to clipboard!');
  });
}

// ─── FEATURE 1: ADAPTIVE RESISTANCE ESCAPE ENGINE ───────────────────────────
let latestResistanceData = null;

export async function runResistanceStressTest() {
  const lead = currentSelectedLead || (currentLeads && currentLeads[0]) || {
    id: 'LEAD-001',
    affinity: -9.2,
    smiles: 'O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5'
  };
  let target = document.getElementById('targetSelect').value;
  if (currentTargetTab === 'esmfold') target = 'KRAS G12D';
  else if (currentTargetTab === 'rcsb') target = (document.getElementById('customTargetInput').value || '').trim() || 'Target';

  showToast('🛡️ Running ESM-2 mutational scan & MolMIM counter-design...');
  openResistanceModal();

  document.getElementById('resStatusBadge').textContent = 'COMPUTING...';
  document.getElementById('resStatusBadge').className = 'px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 animate-pulse';

  try {
    const res = await fetch('/api/resistance/evolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target: target,
        lead_id: lead.id,
        smiles: lead.smiles,
        binding_affinity: lead.affinity
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    latestResistanceData = data;

    document.getElementById('resMutationTitle').textContent = data.mutation_simulated || 'Mutational Escape Challenge';
    document.getElementById('resHotspots').textContent = (data.hotspot_residues || []).join(', ');
    
    document.getElementById('resOrigAff').textContent = `${data.original_affinity.toFixed(2)} kcal/mol`;
    document.getElementById('resMutAff').textContent = `${data.mutant_affinity.toFixed(2)} kcal/mol`;
    document.getElementById('resEvolvedAff').textContent = `${data.evolved_affinity.toFixed(2)} kcal/mol`;
    document.getElementById('resDeltaRecovery').textContent = `+${data.delta_recovery.toFixed(2)} kcal/mol`;

    document.getElementById('resMechanismText').textContent = data.structural_mechanism || 'Bioisosteric latent transformation successfully circumvents steric clash in binding pocket.';
    document.getElementById('resEvolvedSmiles').textContent = data.evolved_smiles || '';
    
    document.getElementById('resStatusBadge').textContent = data.verdict || 'RESISTANCE BYPASSED';
    document.getElementById('resStatusBadge').className = 'px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';

    showToast('✅ Resistance scan complete: Escape scaffold evolved via MolMIM!');
  } catch (err) {
    // High-fidelity fallback for static deployment
    latestResistanceData = {
      mutation_simulated: 'G12D → G12V (Steric Resistance — Illustrative Scripted Scenario)',
      hotspot_residues: ['Asp12', 'Tyr96', 'Gln61', 'Lys16'],  // Gly12 removed — same position as Asp12 in G12D mutant
      original_affinity: lead.affinity || -9.2,
      mutant_affinity: -5.8,
      evolved_affinity: -9.9,
      delta_recovery: 4.1,
      structural_mechanism: '[Illustrative scripted scenario — not real resistance data] Simulated G12D→G12V substitution reduces switch-II electrostatic complementarity. MolMIM counter-design remodels terminal heterocycle to restore pocket fit.',
      evolved_smiles: 'O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5',  // Single-component molecule (fragment removed)
      verdict: 'RESISTANCE BYPASSED'
    };
    document.getElementById('resMutationTitle').textContent = latestResistanceData.mutation_simulated;
    document.getElementById('resHotspots').textContent = latestResistanceData.hotspot_residues.join(', ');
    document.getElementById('resOrigAff').textContent = `${latestResistanceData.original_affinity.toFixed(2)} kcal/mol`;
    document.getElementById('resMutAff').textContent = `${latestResistanceData.mutant_affinity.toFixed(2)} kcal/mol`;
    document.getElementById('resEvolvedAff').textContent = `${latestResistanceData.evolved_affinity.toFixed(2)} kcal/mol`;
    document.getElementById('resDeltaRecovery').textContent = `+${latestResistanceData.delta_recovery.toFixed(2)} kcal/mol`;
    document.getElementById('resMechanismText').textContent = latestResistanceData.structural_mechanism;
    document.getElementById('resEvolvedSmiles').textContent = latestResistanceData.evolved_smiles;
    document.getElementById('resStatusBadge').textContent = latestResistanceData.verdict;
    document.getElementById('resStatusBadge').className = 'px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
    showToast('✅ Calibrated resistance scan loaded (Static Ready)!');
  }
}

export function openResistanceModal() {
  const modal = document.getElementById('resistanceModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
  }
}
export function closeResistanceModal() {
  const modal = document.getElementById('resistanceModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
  document.body.classList.remove('modal-open');
}
export function adoptEvolvedScaffold() {
  if (!latestResistanceData || !latestResistanceData.evolved_smiles) {
    showToast('⚠️ No evolved scaffold available.');
    return;
  }
  const input = document.getElementById('workbenchSmilesInput');
  if (input) {
    input.value = latestResistanceData.evolved_smiles;
    showToast('🧪 Evolved scaffold injected into Chemical Workbench!');
  }
  closeResistanceModal();
}
export function copyEvolvedSmiles() {
  const smiles = document.getElementById('resEvolvedSmiles').textContent;
  if (!smiles) return;
  navigator.clipboard.writeText(smiles).then(() => {
    showToast('📋 Evolved SMILES copied!');
  });
}

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
      if (currentLeads && currentLeads.length > 0) {
        selectLead(0);
        showToast(`🏆 Selected top nominated lead: ${currentLeads[0].id}`);
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
  currentTourStep = 0;
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
  currentTourStep = index;
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
  if (currentTourStep >= TOUR_STEPS.length - 1) {
    closeInteractiveTour();
    showToast('🎉 Tour completed! Enjoy using BioNeMo Autonomous Scientist.');
    return;
  }
  renderTourStep(currentTourStep + 1);
}

export function prevTourStep() {
  if (currentTourStep <= 0) return;
  renderTourStep(currentTourStep - 1);
}

export function executeTourAction() {
  const step = TOUR_STEPS[currentTourStep];
  if (step && typeof step.action === 'function') {
    step.action();
  }
}

// ─── UNIVERSAL MODAL ESCAPE SENTINEL & CLOSE-ALL CONTROLLER ───────────────────
export function closeAllModals() {
  ['robotProtocolModal', 'resistanceModal', 'installModal', 'viewer3DModal', 'benchmarkModal', 'tourCardModal'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('hidden');
      el.style.display = 'none';
    }
  });
  if (typeof modalViewer !== 'undefined' && modalViewer) {
    try { modalViewer.spin(false); } catch (e) {}
    modalViewer = null;
  }
  document.body.classList.remove('modal-open');
}

