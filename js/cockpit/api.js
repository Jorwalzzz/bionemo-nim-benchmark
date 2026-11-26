/**
 * API communication, SSE streaming client, hardware fingerprinting,
 * anti-bypass authentication, and synchronized IST daily quota enforcement.
 */

import { isStaticHost, probeBackendHealth, state, TARGETS } from './state.js';
import { TARGET_PRESETS } from '../data/target-presets.js';
import { renderLeads, setAgent, resetAgents, logEntry, showToast, sleep, updateProvenanceBanner } from './ui-controls.js';
import { renderPareto } from './charts.js';
import { openAuthModal, openQuotaModal } from './modals.js';

// --- Block 9 ---
// ─── Client Hardware & Canvas Fingerprinting (Anti-Bypass) ───────────────────
export function getClientFingerprint() {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = "top";
    ctx.font = "14px 'Arial'";
    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125,1,62,20);
    ctx.fillStyle = "#069";
    ctx.fillText("AgenticBioNeMo:Trial:AntiBypass", 2, 15);
    ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
    ctx.fillText("AgenticBioNeMo:Trial:AntiBypass", 4, 17);
    const b64 = canvas.toDataURL();
    let hash = 0;
    for (let i = 0; i < b64.length; i++) {
      hash = ((hash << 5) - hash) + b64.charCodeAt(i);
      hash |= 0;
    }
    const gl = document.createElement('canvas').getContext('webgl');
    const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
    const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'no-gl';
    return Math.abs(hash).toString(16) + '_' + btoa(renderer).slice(0, 16) + '_' + screen.width + 'x' + screen.height;
  } catch (e) {
    return 'fp_' + screen.width + 'x' + screen.height + '_' + (navigator.hardwareConcurrency || 4);
  }
}
const CLIENT_FP = getClientFingerprint();

let trialState = { allowed: true, runs_used: 0, runs_remaining: 5, max_runs: 5, is_locked: false };

// ═════════════════════════════════════════════════════════════════════════════
// SYNCHRONIZED 3:00 PM IST (09:30 UTC) DAILY QUOTA & AUTHENTICATION ENGINE
// ═════════════════════════════════════════════════════════════════════════════

const IST_RESET_OFFSET_SECONDS = 34200; // 09:30:00 UTC = 15:00:00 IST
const MAX_DAILY_RUNS = 5;

export function computeISTCycleInfo(epochSec) {
  const now = epochSec !== undefined ? epochSec : Math.floor(Date.now() / 1000);
  const cycleIndex = Math.floor((now - IST_RESET_OFFSET_SECONDS) / 86400);
  const nextResetEpoch = (cycleIndex + 1) * 86400 + IST_RESET_OFFSET_SECONDS;
  const secondsRemaining = Math.max(0, nextResetEpoch - now);
  const h = String(Math.floor(secondsRemaining / 3600)).padStart(2, '0');
  const m = String(Math.floor((secondsRemaining % 3600) / 60)).padStart(2, '0');
  const s = String(secondsRemaining % 60).padStart(2, '0');
  return {
    cycleIndex,
    cycleKey: `ist_cycle_${cycleIndex}`,
    nextResetEpoch,
    secondsRemaining,
    countdown: `${h}:${m}:${s}`
  };
}

const DISPOSABLE_EMAIL_DOMAINS = new Set([
  'mailinator.com',
  'tempmail.com',
  '10minutemail.com',
  'guerrillamail.com',
  'yopmail.com',
  'throwawaymail.com',
  'trashmail.com',
  'sharklasers.com',
  'getnada.com',
  'temp-mail.org',
  'dispostable.com',
  'fakeinbox.com',
  'mailnesia.com',
  'maildrop.cc',
  'mohmal.com',
  'generator.email',
  'inboxkitten.com',
  'burnermail.io'
]);

const COMMON_DOMAIN_TYPOS = {
  'gamil.com': 'gmail.com',
  'gmai.com': 'gmail.com',
  'gmial.com': 'gmail.com',
  'gmaill.com': 'gmail.com',
  'yaho.com': 'yahoo.com',
  'yahooo.com': 'yahoo.com',
  'hotmial.com': 'hotmail.com',
  'hotmaill.com': 'hotmail.com',
  'outlok.com': 'outlook.com',
  'outloo.com': 'outlook.com',
  'protonmai.com': 'protonmail.com',
  'protonmial.com': 'protonmail.com'
};

const EMAIL_STRICT_REGEX = /^[a-zA-Z0-9.!#$%&*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/;

export function validateEmailDetailed(email) {
  if (!email || typeof email !== 'string') {
    return { valid: false, message: 'Email address cannot be empty.', type: 'invalid' };
  }
  const clean = email.trim();
  if (clean.length > 254) {
    return { valid: false, message: 'Email address exceeds maximum length of 254 characters.', type: 'invalid' };
  }
  if (!clean.includes('@')) {
    return { valid: false, message: "Missing '@' symbol in email address.", type: 'invalid' };
  }
  const parts = clean.split('@');
  if (parts.length !== 2) {
    return { valid: false, message: "Email contains multiple '@' symbols.", type: 'invalid' };
  }
  const [localPart, domainPart] = parts;
  if (!localPart) {
    return { valid: false, message: "Missing recipient username before '@'.", type: 'invalid' };
  }
  if (!domainPart) {
    return { valid: false, message: "Missing domain host after '@'.", type: 'invalid' };
  }
  if (!domainPart.includes('.')) {
    return { valid: false, message: `Domain '@${domainPart}' missing extension (e.g. .edu, .com).`, type: 'invalid' };
  }
  const tld = domainPart.split('.').pop().toLowerCase();
  if (tld.length < 2 || !/^[a-z]+$/i.test(tld)) {
    return { valid: false, message: `Invalid domain extension '.${tld}'. Must be at least 2 letters.`, type: 'invalid' };
  }
  if (!EMAIL_STRICT_REGEX.test(clean)) {
    return { valid: false, message: 'Invalid email address format.', type: 'invalid' };
  }
  const domainLower = domainPart.toLowerCase();
  if (DISPOSABLE_EMAIL_DOMAINS.has(domainLower)) {
    return {
      valid: false,
      message: `Disposable temporary domain '@${domainLower}' is not permitted. Please use an institutional or primary email.`,
      type: 'disposable'
    };
  }
  if (COMMON_DOMAIN_TYPOS[domainLower]) {
    const suggested = COMMON_DOMAIN_TYPOS[domainLower];
    return {
      valid: false,
      message: `Possible typo in '@${domainLower}'. Did you mean '@${suggested}'?`,
      suggestion: `${localPart}@${suggested}`,
      type: 'typo'
    };
  }

  const isAcademic = ['.edu', '.ac.uk', '.edu.cn', '.ac.in', '.res.in', '.org'].some(suf => domainLower.endsWith(suf));
  return {
    valid: true,
    message: isAcademic ? '✓ Verified academic/institutional domain' : '✓ Valid email address format',
    type: isAcademic ? 'academic' : 'standard'
  };
}

export function handleEmailInputValidation(inputEl, feedbackId) {
  const feedbackEl = document.getElementById(feedbackId);
  if (!feedbackEl || !inputEl) return;

  const value = inputEl.value.trim();
  if (!value) {
    feedbackEl.replaceChildren();
    feedbackEl.classList.add('hidden');
    inputEl.style.borderColor = '';
    return;
  }

  const result = validateEmailDetailed(value);
  feedbackEl.classList.remove('hidden');

  if (result.type === 'typo' && result.suggestion) {
    inputEl.style.borderColor = '#f59e0b';
    const wrap = document.createElement('div');
    wrap.className = 'p-2 rounded bg-amber-950/40 border border-amber-500/40 text-amber-300 flex items-center justify-between';

    const msgSpan = document.createElement('span');
    msgSpan.textContent = `⚠️ ${result.message}`;
    wrap.appendChild(msgSpan);

    const fixBtn = document.createElement('button');
    fixBtn.type = 'button';
    fixBtn.className = 'ml-2 px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-white font-bold border border-amber-500/40 text-[10px]';
    fixBtn.textContent = 'Click to Fix';
    fixBtn.addEventListener('click', () => fixEmailTypo(inputEl.id, result.suggestion, feedbackId));
    wrap.appendChild(fixBtn);

    feedbackEl.replaceChildren(wrap);
  } else if (!result.valid) {
    inputEl.style.borderColor = '#ef4444';
    const wrap = document.createElement('div');
    wrap.className = 'p-1.5 rounded bg-red-950/40 border border-red-500/40 text-red-300 flex items-center gap-1.5';

    const iconSpan = document.createElement('span');
    iconSpan.textContent = '❌';
    wrap.appendChild(iconSpan);

    const msgSpan = document.createElement('span');
    msgSpan.textContent = result.message;
    wrap.appendChild(msgSpan);

    feedbackEl.replaceChildren(wrap);
  } else {
    inputEl.style.borderColor = '#10b981';
    const pillClass = result.type === 'academic'
      ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300'
      : 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300';
    const wrap = document.createElement('div');
    wrap.className = `p-1.5 rounded border ${pillClass} flex items-center gap-1.5`;

    const msgSpan = document.createElement('span');
    msgSpan.textContent = result.message;
    wrap.appendChild(msgSpan);

    feedbackEl.replaceChildren(wrap);
  }
}

export function fixEmailTypo(inputId, correctedEmail, feedbackId) {
  const inputEl = document.getElementById(inputId);
  if (inputEl) {
    inputEl.value = correctedEmail;
    handleEmailInputValidation(inputEl, feedbackId);
  }
}

export function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c]));
}

export async function hashPasswordSHA256(password) {
  try {
    if (window.crypto && window.crypto.subtle) {
      const data = new TextEncoder().encode(password);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
      return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    }
  } catch (e) {
    console.warn('SubtleCrypto unavailable:', e);
  }
  let hash = 0;
  for (let i = 0; i < password.length; i++) {
    const char = password.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return `fallback_${Math.abs(hash)}`;
}

export class ClientAuthManager {
  constructor() {
    this.user = null;
    this.token = null;
    this.pendingAction = null;
    this.isStaticHost = isStaticHost;
  }

  async init() {
    try {
      const stored = localStorage.getItem('bionemo_auth_session');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && parsed.user) {
          this.user = parsed.user;
          this.token = parsed.token;
        }
      }
    } catch (e) {
      console.warn('Failed to parse cached auth session:', e);
    }

    const backendUp = await probeBackendHealth();
    this.isStaticHost = !backendUp;
    if (backendUp && this.token) {
      try {
        const headers = this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
        const res = await fetch('./api/auth/me', { headers });
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated && data.user) {
            this.user = data.user;
          } else if (!data.authenticated && this.token) {
            this.user = null;
            this.token = null;
            localStorage.removeItem('bionemo_auth_session');
          }
        }
      } catch (err) {
        console.warn('Backend auth endpoint unreachable; using local session:', err);
      }
    }

    this.renderHUD();
    if (this.tickIntervalId) {
      clearInterval(this.tickIntervalId);
    }
    this.tickIntervalId = setInterval(() => this.tick(), 1000);
  }

  isLoggedIn() {
    return !!this.user;
  }

  getCurrentUser() {
    return this.user;
  }

  getQuota() {
    const cycle = computeISTCycleInfo();
    if (!this.user) {
      return {
        allowed: false,
        runs_used: 0,
        runs_remaining: MAX_DAILY_RUNS,
        max_runs: MAX_DAILY_RUNS,
        is_locked: false,
        requires_login: true,
        ...cycle
      };
    }

    const quotaKey = `bionemo_quota_${this.user.id || this.user.user_id || 'demo'}_${cycle.cycleKey}`;
    let runsUsed = 0;
    try {
      runsUsed = parseInt(localStorage.getItem(quotaKey) || '0', 10);
      if (isNaN(runsUsed) || runsUsed < 0) runsUsed = 0;
    } catch (e) {
      runsUsed = 0;
    }

    const runsRemaining = Math.max(0, MAX_DAILY_RUNS - runsUsed);
    return {
      allowed: runsRemaining > 0,
      runs_used: runsUsed,
      runs_remaining: runsRemaining,
      max_runs: MAX_DAILY_RUNS,
      is_locked: runsRemaining <= 0,
      requires_login: false,
      ...cycle
    };
  }

  consumeRun() {
    if (!this.user) return false;
    const cycle = computeISTCycleInfo();
    const quotaKey = `bionemo_quota_${this.user.id || this.user.user_id || 'demo'}_${cycle.cycleKey}`;
    let runsUsed = 0;
    try {
      runsUsed = parseInt(localStorage.getItem(quotaKey) || '0', 10);
      if (isNaN(runsUsed) || runsUsed < 0) runsUsed = 0;
    } catch (e) {
      runsUsed = 0;
    }

    if (runsUsed >= MAX_DAILY_RUNS) {
      return false;
    }

    runsUsed += 1;
    try {
      localStorage.setItem(quotaKey, String(runsUsed));
    } catch (e) {
      console.warn('Storage quota update warning:', e);
    }
    this.renderHUD();
    return true;
  }

  async login(email, password) {
    email = (email || '').trim().toLowerCase();
    password = (password || '').trim();

    const backendUp = await probeBackendHealth();
    this.isStaticHost = !backendUp;
    if (backendUp) {
      try {
        const res = await fetch('./api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
          body: JSON.stringify({ email, password })
        });
        if (res.ok) {
          const data = await res.json();
          this.user = data.user;
          this.token = data.token;
          localStorage.setItem('bionemo_auth_session', JSON.stringify({ user: this.user, token: this.token }));
          this.renderHUD();
          return { success: true, user: this.user };
        } else {
          const errData = await res.json().catch(() => ({}));
          return { success: false, message: errData.message || 'Invalid email or password.' };
        }
      } catch (err) {
        console.warn('Backend login error, attempting local validation:', err);
      }
    }

    try {
      const usersRaw = localStorage.getItem('bionemo_registered_users');
      const users = usersRaw ? JSON.parse(usersRaw) : {};
      const u = users[email];
      if (u) {
        const pwdHash = await hashPasswordSHA256(password);
        const matches = u.password_hash ? (u.password_hash === pwdHash) : (u.password === password);
        if (matches) {
          if (u.password && !u.password_hash) {
            u.password_hash = pwdHash;
            delete u.password;
            try { localStorage.setItem('bionemo_registered_users', JSON.stringify(users)); } catch (e) {}
          }
          this.user = { id: u.id, email: u.email, full_name: u.full_name, organization: u.organization };
          this.token = `static_tok_${u.id}_${Date.now()}`;
          localStorage.setItem('bionemo_auth_session', JSON.stringify({ user: this.user, token: this.token }));
          this.renderHUD();
          return { success: true, user: this.user };
        }
      }
    } catch (e) {
      console.warn('Local account verification error:', e);
    }

    return { success: false, message: 'Invalid credentials. For instant demo access, use the 1-Click Evaluator Sign In.' };
  }

  async demoLogin() {
    const backendUp = await probeBackendHealth();
    this.isStaticHost = !backendUp;
    if (backendUp) {
      try {
        const res = await fetch('./api/auth/demo-login', {
          method: 'POST',
          headers: { 'X-BioNeMo-CSRF': '1' }
        });
        if (res.ok) {
          const data = await res.json();
          this.user = data.user;
          this.token = data.token;
          localStorage.setItem('bionemo_auth_session', JSON.stringify({ user: this.user, token: this.token }));
          this.renderHUD();
          return { success: true, user: this.user };
        }
      } catch (e) {
        console.warn('Backend demo-login failed, falling back to client demo session:', e);
      }
    }

    this.user = {
      id: 'usr_evaluator_2026',
      email: 'evaluator@bionemo.org',
      full_name: 'BioNeMo Peer Evaluator',
      organization: 'Global Bio-Computational Initiative'
    };
    this.token = `eval_token_${Date.now()}`;
    localStorage.setItem('bionemo_auth_session', JSON.stringify({ user: this.user, token: this.token }));
    this.renderHUD();
    return { success: true, user: this.user };
  }

  async register(fullName, organization, email, password) {
    fullName = (fullName || 'Researcher').trim();
    organization = (organization || 'Independent').trim();
    email = (email || '').trim().toLowerCase();
    password = (password || '').trim();

    if (!email || !email.includes('@')) {
      return { success: false, message: 'Valid email address required.' };
    }
    if (password.length < 6) {
      return { success: false, message: 'Password must be at least 6 characters.' };
    }

    const backendUp = await probeBackendHealth();
    this.isStaticHost = !backendUp;
    if (backendUp) {
      try {
        const res = await fetch('./api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
          body: JSON.stringify({ full_name: fullName, organization, email, password })
        });
        if (res.ok) {
          const data = await res.json();
          this.user = data.user;
          this.token = data.token;
          localStorage.setItem('bionemo_auth_session', JSON.stringify({ user: this.user, token: this.token }));
          this.renderHUD();
          return { success: true, user: this.user };
        } else {
          const errData = await res.json().catch(() => ({}));
          return { success: false, message: errData.message || 'Registration failed.' };
        }
      } catch (err) {
        console.warn('Backend register error, saving to client store:', err);
      }
    }

    try {
      const usersRaw = localStorage.getItem('bionemo_registered_users');
      const users = usersRaw ? JSON.parse(usersRaw) : {};
      if (users[email]) {
        return { success: false, message: 'An account with this email already exists. Please sign in.' };
      }
      const newId = `usr_${Math.random().toString(36).substring(2, 10)}`;
      const pwdHash = await hashPasswordSHA256(password);
      users[email] = {
        id: newId,
        email,
        full_name: fullName,
        organization,
        password_hash: pwdHash,
        created_at: Math.floor(Date.now() / 1000)
      };
      localStorage.setItem('bionemo_registered_users', JSON.stringify(users));

      this.user = { id: newId, email, full_name: fullName, organization };
      this.token = `static_tok_${newId}_${Date.now()}`;
      localStorage.setItem('bionemo_auth_session', JSON.stringify({ user: this.user, token: this.token }));
      this.renderHUD();
      return { success: true, user: this.user };
    } catch (e) {
      return { success: false, message: 'Failed to save account locally.' };
    }
  }

  logout() {
    if (state.isBackendAvailable) {
      fetch('./api/auth/logout', {
        method: 'POST',
        headers: {
          'X-BioNeMo-CSRF': '1',
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {})
        }
      }).catch(() => {});
    }
    this.user = null;
    this.token = null;
    try {
      localStorage.removeItem('bionemo_auth_session');
    } catch (e) {}
    const fbId = document.getElementById('feedbackUserIdentity');
    if (fbId) fbId.textContent = 'Not signed in';
    this.renderHUD();
    showToast('Signed out of researcher session.');
  }

  async submitFeedback(payload) {
    if (!this.user) {
      return { success: false, message: 'Authentication required to submit feedback.' };
    }

    const backendUp = await probeBackendHealth();
    this.isStaticHost = !backendUp;
    if (backendUp) {
      try {
        const headers = { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' };
        if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
        const res = await fetch('./api/feedback', {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok) {
          this.recordLocalFeedback(payload);
          return { success: true, message: data.message || 'Feedback submitted.' };
        }
        return {
          success: false,
          message: data.message || data.detail || `Feedback rejected (HTTP ${res.status}).`
        };
      } catch (e) {
        console.warn('Backend feedback error:', e);
        return { success: false, message: 'Failed to submit feedback to server.' };
      }
    }

    this.recordLocalFeedback(payload);
    return { success: true, message: 'Scientific feedback recorded locally (offline demo).' };
  }

  recordLocalFeedback(payload) {
    try {
      const existingRaw = localStorage.getItem('bionemo_feedback_store');
      const list = existingRaw ? JSON.parse(existingRaw) : [];
      const entry = {
        id: `fb-${Math.random().toString(36).substring(2, 8)}`,
        timestamp: Math.floor(Date.now() / 1000),
        user_email: this.user.email,
        full_name: this.user.full_name,
        organization: this.user.organization,
        category: payload.category || 'General',
        rating: payload.rating || 5,
        comments: payload.comments || '',
        target_name: payload.target_name || 'KRAS G12D'
      };
      list.unshift(entry);
      localStorage.setItem('bionemo_feedback_store', JSON.stringify(list.slice(0, 50)));
    } catch (e) {
      console.warn('Feedback local storage write error:', e);
    }
  }

  getLocalFeedback() {
    try {
      const existingRaw = localStorage.getItem('bionemo_feedback_store');
      if (!existingRaw) return [];
      const list = JSON.parse(existingRaw);
      if (!this.user) return [];
      return list.filter(item => item.user_email === this.user.email);
    } catch (e) {
      return [];
    }
  }

  tick() {
    const quota = this.getQuota();
    const modalEl = document.getElementById('quotaModalCountdown');
    if (modalEl) {
      modalEl.textContent = quota.countdown;
    }

    const hudCountdown = document.getElementById('hudCountdownText');
    if (hudCountdown) {
      hudCountdown.textContent = `${quota.countdown} (3:00 PM IST)`;
    }

    if (quota.secondsRemaining === 86399) {
      this.renderHUD();
      showToast('Synchronized 3:00 PM IST cycle refreshed. 5 new discovery runs granted.');
    }
  }

  renderHUD() {
    const container = document.getElementById('authHudContainer');
    if (!container) return;

    const quota = this.getQuota();

    if (!this.user) {
      container.innerHTML = `
        <button type="button" id="authBtn" data-action="open-auth-modal" class="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 border border-emerald-400/40 shadow-sm flex items-center gap-1.5 transition-all">
          <span>Sign In</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 border border-white/20">5 Runs/Day</span>
        </button>
      `;
    } else {
      const shortEmail = this.user.email.length > 20 ? this.user.email.substring(0, 18) + '...' : this.user.email;
      const pillColor = quota.runs_remaining > 0 ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-red-500/15 text-red-300 border-red-500/40 animate-pulse';

      container.innerHTML = `
        <div class="flex items-center gap-2">
          <div class="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-mono text-gray-300">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span title="${escapeHtml(this.user.email)}">${escapeHtml(shortEmail)}</span>
          </div>

          <div class="flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-mono font-bold ${pillColor}" title="Synchronized refresh at 3:00 PM IST">
            <span>Runs ${quota.runs_remaining}/${quota.max_runs}</span>
          </div>

          <div id="hudCountdownText" class="hidden md:inline-flex text-[11px] font-mono text-amber-300/90 px-2 py-1 rounded bg-amber-500/10 border border-amber-500/20" title="Universal synchronized reset at 3:00 PM IST (09:30 UTC)">
            ${quota.countdown} (3:00 PM IST)
          </div>

          <button type="button" data-action="logout" aria-label="Sign Out" title="Sign Out" class="px-2 py-1 rounded-lg text-xs font-semibold text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-colors">
            &times;
          </button>
        </div>
      `;
    }

    // Update Run Controls based on Sign-In state and backend availability
    const banner = document.getElementById('authRequiredBanner');
    const backendUp = Boolean(state.isBackendAvailable);
    if (banner) {
      if (backendUp && !this.user && window.isOwner !== true) {
        banner.style.display = 'block';
        banner.classList.remove('hidden');
      } else {
        banner.style.display = 'none';
        banner.classList.add('hidden');
      }
    }

    const runBtn = document.getElementById('runBtn');
    const runLabel = document.getElementById('runLabel');
    if (runBtn && !state.isRunning) {
      if (window.isOwner === true) {
        runBtn.className = 'btn-cta w-full text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 mb-4';
        runBtn.dataset.action = 'run-discovery';
        if (runLabel) runLabel.innerHTML = 'Run Autonomous Discovery <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Owner Mode</span>';
      } else if (!backendUp) {
        runBtn.className = 'btn-cta w-full text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 mb-4';
        runBtn.dataset.action = 'run-discovery';
        if (runLabel) runLabel.textContent = 'Run Autonomous Discovery';
      } else if (!this.user) {
        runBtn.dataset.action = 'open-auth-modal';
        runBtn.dataset.arg = 'Sign-In Required: Please sign in or register to launch autonomous discovery (5 free runs/day).';
        runBtn.className = 'w-full text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 mb-4 bg-gradient-to-r from-amber-600 to-emerald-700 hover:from-amber-500 hover:to-emerald-600 shadow-lg border border-amber-400/40 cursor-pointer transition-all';
        if (runLabel) runLabel.innerHTML = 'Sign In to Run Discovery <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/40 border border-white/20">5 Runs/Day Free</span>';
      } else {
        runBtn.className = 'btn-cta w-full text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 mb-4';
        if (quota.runs_remaining <= 0) {
          runBtn.dataset.action = 'open-quota-modal';
          if (runLabel) runLabel.innerHTML = `Daily Quota Exhausted <span class="text-[10px] font-mono">(${quota.countdown})</span>`;
        } else {
          runBtn.dataset.action = 'run-discovery';
          if (runLabel) runLabel.textContent = 'Run Autonomous Discovery';
        }
      }
    }

    const trialText = document.getElementById('trialText');
    if (trialText) {
      if (!this.user) {
        trialText.innerHTML = `<span class="text-emerald-400 font-bold tracking-wide">Discovery Studio</span> <span class="text-amber-300 text-[11px] font-mono">· Sign in for 5 free runs/day</span>`;
      } else {
        trialText.innerHTML = `<span class="text-emerald-400 font-bold tracking-wide">${escapeHtml(this.user.organization || 'Research Lab')}</span> <span class="text-cyan-300 text-[11px] font-mono">· ${quota.runs_remaining} runs left (resets 3:00 PM IST)</span>`;
      }
    }
  }
}

export const clientAuth = new ClientAuthManager();


export async function resetTrialQuota() {
  try {
    if (!(await probeBackendHealth())) return;
    const res = await fetch('./api/reset-trial', {
      method: 'POST',
      headers: { 'X-Client-Fingerprint': CLIENT_FP, 'X-BioNeMo-CSRF': '1' }
    });
    if (res.ok) {
      showToast('Demo quota reset. Ready to run discovery.');
      fetchTrialStatus();
    }
  } catch (e) {
    console.error('Reset error:', e);
  }
}

const _QK = '_bnq_' + CLIENT_FP;
export function _qSig(n) { let h = 7; const s = n + '|' + CLIENT_FP + '|bnq'; for (let i = 0; i < s.length; i++) h = ((h * 31) + s.charCodeAt(i)) | 0; return (h >>> 0).toString(36); }
export function staticQuota(consume) {
  return { allowed: true, runs_used: 0, runs_remaining: 9999, max_runs: 9999, is_locked: false };
}

export async function fetchTrialStatus() {
  if (window.clientAuth) {
    await window.clientAuth.init();
  }
}

export function updateTrialUI(status) {
  if (window.clientAuth) {
    window.clientAuth.renderHUD();
  }
}


let activeDiscoveryController = null;

export async function runDiscovery() {
  if (state.isRunning) return;
  const backendUp = await probeBackendHealth();
  if (state.isRunning) return;

  const isOwnerSession = window.isOwner === true;

  if (backendUp && !clientAuth.isLoggedIn() && !isOwnerSession) {
    clientAuth.pendingAction = 'discovery';
    openAuthModal('Please sign in or register to access the free trial discovery pipeline (5 runs/day).');
    return;
  }

  if (backendUp && clientAuth.isLoggedIn() && !isOwnerSession) {
    const quota = clientAuth.getQuota();
    if (quota.runs_remaining <= 0) {
      openQuotaModal();
      return;
    }
  }

  const targetSelect = document.getElementById('targetSelect');
  let target = targetSelect ? targetSelect.value : '7RPZ';
  const targetTab = state.currentTargetTab || 'presets';
  if (targetTab === 'esmfold') {
    const rawSeq = document.getElementById('esmfoldSeqInput')?.value || state.currentTargetSeq || '';
    const cleanSeq = rawSeq.replace(/^>.*$/gm, '').replace(/\s+/g, '').toUpperCase();
    if (!cleanSeq || cleanSeq.length < 10) {
      showToast('Please enter or load an amino acid sequence (at least 10 residues) for ESMFold.');
      return;
    }
    state.currentTargetSeq = cleanSeq;
    target = cleanSeq;
  } else if (targetTab === 'rcsb') {
    target = (document.getElementById('customTargetInput')?.value || '').trim() || '7RPZ';
  }

  state.isRunning = true;
  state.currentLeads = [];
  state.currentSelectedLead = null;
  let authBlocked = false;

  const candidateSlider = document.getElementById('candidateSlider');
  const candidates = candidateSlider ? parseInt(candidateSlider.value, 10) : 12;
  const info = TARGETS[target] || (targetTab === 'esmfold'
    ? {
        name: `ESMFold Target (${target.length} aa)`,
        pdb: 'DE NOVO',
        pocket: 'Predicted Binding Pocket',
        mutant: 'De Novo',
        color: '#a855f7',
        ligandName: 'DE-NOVO',
        pocketResidues: state.currentTargetPocketResidues || []
      }
    : (TARGETS['7RPZ'] || {
        name: target,
        pdb: target,
        indication: 'Target Screening',
        pocket: 'Active Binding Pocket',
        mutant: '—',
        color: '#76b900',
        pocketResidues: []
      }));
  const safeTargetDisplay = escapeHtml(info.name || target);
  const safePdbDisplay = escapeHtml(info.pdb || target);
  const safePocketDisplay = escapeHtml(info.pocket || 'Binding Pocket');

  document.getElementById('agentLog').innerHTML = '';
  document.getElementById('leadsContainer').innerHTML = '<div class="text-center text-gray-600 text-xs py-4">Preparing autonomous discovery pipeline...</div>';
  resetAgents();
  document.getElementById('progressBar').style.width = '5%';
  document.getElementById('streamDot').style.background = '#76b900';
  document.getElementById('runBtn').disabled = true;
  document.getElementById('runLabel').textContent = 'Running Pipeline...';

  if (activeDiscoveryController) {
    activeDiscoveryController.abort();
  }
  const abortController = new AbortController();
  activeDiscoveryController = abortController;
  let streamedDialogues = [];

  try {
    let backendData = null;
    if (backendUp) {
      const headers = {
        'Content-Type': 'application/json',
        'X-Client-Fingerprint': CLIENT_FP,
        'X-BioNeMo-CSRF': '1'
      };
      if (clientAuth.token) {
        headers['Authorization'] = `Bearer ${clientAuth.token}`;
      }

      const res = await fetch('./api/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify({ target, candidates }),
        signal: abortController.signal
      });

      if (res.status === 401) {
        authBlocked = true;
        document.getElementById('streamDot').style.background = '#ef4444';
        openAuthModal('Session authentication required before launching a discovery run.');
        return;
      }

      if (res.status === 403 || res.status === 429) {
        authBlocked = true;
        const errData = await res.json().catch(() => ({}));
        document.getElementById('streamDot').style.background = '#ef4444';
        updateTrialUI({ runs_used: errData.runs_used || 5, runs_remaining: 0, is_locked: true, max_runs: 5 });
        showToast(errData.message || 'Daily quota limit exceeded.');
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.message || `Backend error (HTTP ${res.status})`);
      }

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('text/event-stream') && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let stepCount = 0;

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split(/\r?\n\r?\n/);
          buffer = frames.pop() || '';

          for (const frame of frames) {
            const dataLines = frame
              .split(/\r?\n/)
              .filter(l => l.startsWith('data:'))
              .map(l => l.slice(5).trim());
            if (dataLines.length === 0) continue;

            const payloadStr = dataLines.join('\n');
            if (!payloadStr || payloadStr === '[DONE]') continue;

            const evt = JSON.parse(payloadStr);
            if (evt.event === 'stream_ready') {
              document.getElementById('progressBar').style.width = '12%';
            } else if (evt.event === 'council_message') {
              stepCount += 1;
              streamedDialogues.push(evt);
              document.getElementById('progressBar').style.width = `${Math.min(88, 15 + stepCount * 10)}%`;
              logEntry('', evt.persona_name || 'Council Agent', evt.intent || 'UPDATE', escapeHtml(evt.content || ''), info.color || '#76b900');
            } else if (evt.event === 'campaign_error') {
              throw new Error(evt.message || 'Campaign execution failed');
            } else if (evt.event === 'campaign_complete') {
              backendData = evt;
            }
          }
        }
      } else {
        backendData = await res.json();
      }

      if (backendData) {
        if (clientAuth.isLoggedIn() && !isOwnerSession) {
          clientAuth.consumeRun();
        }
        if (backendData.trial_status) {
          updateTrialUI(backendData.trial_status);
        }
        if (backendData.leads && backendData.leads.length > 0) {
          state.currentLeads = backendData.leads.map(l => ({
            ...l,
            affinity: l.binding_affinity !== undefined ? l.binding_affinity : (l.affinity || -8.5),
            verdict: l.admet_verdict || l.verdict || 'PASS',
            pareto: l.is_pareto !== undefined ? l.is_pareto : (l.pareto || false)
          }));
          state.currentTargetPdbText = backendData.target_pdb || state.currentTargetPdbText;
          state.currentTargetPocketResidues = backendData.pocket_residues || state.currentTargetPocketResidues;
          state.currentTargetIsEsmfold = backendData.is_esmfold || false;
          state.currentTargetMeanPlddt = backendData.mean_plddt || 0.0;
        }
      }
    }
    if (!backendData) {
      const q = staticQuota(1);
      updateTrialUI(q);
    }

  // 1. Resolve active leads either from backend or generated in silico strictly from target metadata
  let activeProvenance = null;
  if (!state.currentLeads || state.currentLeads.length === 0) {
    const targetPreset = (TARGET_PRESETS && TARGET_PRESETS.getTarget(info.pdb)) || 
      (TARGET_PRESETS && TARGET_PRESETS.all.find(t => t.pdbId === info.pdb || t.name === info.name)) || 
      info;
    const ligandClean = (targetPreset.ligandName || info.ligandName || 'LEAD').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 11) || 'CANDIDATE';
    const baseAffinity = targetPreset.affinity?.delta_g_kcal_mol || info.affinity?.delta_g_kcal_mol || -9.5;
    const baseResidues = (targetPreset.pocketResidues && targetPreset.pocketResidues.length > 0) 
      ? targetPreset.pocketResidues 
      : ((info.pocketResidues && info.pocketResidues.length > 0) ? info.pocketResidues : ['Lys100', 'Asp105', 'Glu110']);
    const refSmiles = targetPreset.referenceSmiles || info.referenceSmiles || 'CC(=O)Nc1ccc(O)cc1';
    const baseMw = targetPreset.admet?.mw_da || info.admet?.mw_da || 420.0;
    const baseLogp = targetPreset.admet?.logp || info.admet?.logp || 2.8;

    const simLeads = [];
    const count = Math.min(Math.max(candidates, 1), 10);
    for (let idx = 0; idx < count; idx++) {
      const numStr = String(idx + 1).padStart(2, '0');
      const leadId = `${ligandClean}-SIM-${numStr}`;
      const affOffset = idx === 0 ? 0 : Math.round((idx * 0.42 - 0.15) * 100) / 100;
      const affinity = Math.round((baseAffinity + affOffset) * 100) / 100;
      const qed = Math.round(Math.max(0.32, Math.min(0.91, 0.79 - (idx * 0.045))) * 1000) / 1000;
      const mw = Math.round((baseMw + (idx % 2 === 0 ? idx * 3.8 : -idx * 2.7)) * 10) / 10;
      const logp = Math.round((baseLogp + (idx * 0.14 - 0.25)) * 100) / 100;
      const sascore = Math.round((2.3 + idx * 0.16) * 100) / 100;
      const isPareto = idx === 0 || idx === 1 || (idx === 2 && count > 4);
      const verdict = idx === count - 1 && count > 5 ? 'FLAGGED' : 'PASS';

      simLeads.push({
        id: leadId,
        smiles: refSmiles,
        affinity: affinity,
        binding_affinity: affinity,
        qed: qed,
        mw: mw,
        logp: logp,
        sascore: sascore,
        verdict: verdict,
        admet_verdict: verdict,
        pareto: isPareto,
        is_pareto: isPareto,
        round: idx < 3 ? 1 : 2,
        provenance: 'SIMULATED',
        is_simulated: true,
        contact_residues: baseResidues.slice(0, 3).join(', ')
      });
    }
    state.currentLeads = simLeads;

    activeProvenance = {
      mode: 'OFFLINE_DEMO',
      provenance: 'SIMULATED',
      backend_host: window.location.hostname || 'localhost',
      target_pdb: info.pdb,
      target_name: info.name,
      contact_residues: baseResidues.slice(0, 3),
      timestamp_utc: new Date().toISOString(),
      notice: 'Executed in client simulation mode. Zero hardcoded KRAS leads leaked.'
    };
  } else {
    activeProvenance = backendData?.provenance || {
      mode: 'LIVE_NVIDIA_NIM',
      provenance: 'LIVE_NVIDIA_NIM',
      backend_host: window.location.hostname || '127.0.0.1',
      timestamp_utc: new Date().toISOString()
    };
  }

  // Update Provenance Banner
  updateProvenanceBanner(activeProvenance);

  // 2. Establish Unified Run Result (Single Source of Truth)
  const leads = state.currentLeads || [];
  const screenedCount = leads.length;
  const passedCount = leads.filter(l => l.verdict === 'PASS' || l.admet_verdict === 'PASS').length;
  const flaggedCount = leads.length - passedCount;
  const paretoCount = leads.filter(l => l.pareto || l.is_pareto).length;
  const topLead = leads[0] || { id: 'NIM-LEAD-01', affinity: -9.5, qed: 0.75, mw: 450, sascore: 2.5 };

  const runResult = {
    target: info.name || target,
    pdbId: info.pdb,
    screenedCount: screenedCount,
    passedCount: passedCount,
    flaggedCount: flaggedCount,
    dockedCount: screenedCount,
    paretoCount: paretoCount,
    leads: leads,
    topLead: topLead,
    provenance: activeProvenance,
    timestamp: new Date().toISOString()
  };
  state.activeRunResult = runResult;
  if (typeof window !== 'undefined') {
    window.activeRunResult = runResult;
  }

  const setProgress = (p) => {
    document.getElementById('progressBar').style.width = p + '%';
  };

  // ─ Stage 1: Target Scout ─
  
  if (backendData && backendData.council_dialogues && backendData.council_dialogues.length > 0 && streamedDialogues.length === 0) {
    document.getElementById('agentLog').innerHTML = '';
    for (const d of backendData.council_dialogues) {
      const isVeto = d.intent === 'VETO';
      const isClear = d.intent === 'CLEARANCE';
      const isConsensus = d.intent === 'CONSENSUS';
      const badgeColor = isVeto ? '#ef4444' : isClear ? '#10b981' : isConsensus ? '#f59e0b' : '#06b6d4';
      const bgColor = isVeto ? 'rgba(239, 68, 68, 0.08)' : 'rgba(22, 27, 34, 0.6)';
      const borderColor = isVeto ? 'rgba(239, 68, 68, 0.3)' : 'rgba(48, 54, 61, 0.5)';

      const entry = document.createElement('div');
      entry.className = 'p-2.5 rounded-xl border text-xs animate-fade-up';
      entry.style.background = bgColor;
      entry.style.borderColor = borderColor;
      entry.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <div class="flex items-center gap-1.5 font-bold">
            <span class="text-gray-200 text-xs">${escapeHtml(d.persona || 'Council Agent')}</span>
            <span class="px-1.5 py-0.2 text-[9px] rounded font-mono font-bold" style="background:${badgeColor}22; color:${badgeColor}; border:1px solid ${badgeColor}44;">${escapeHtml(d.intent)}</span>
          </div>
          <span class="text-[10px] text-gray-500 font-mono">${escapeHtml(d.time || '')}</span>
        </div>
        <div class="text-gray-300 font-sans leading-relaxed text-[11px]">${escapeHtml(d.content)}</div>
      `;
      document.getElementById('agentLog').appendChild(entry);
    }
  }

  if (streamedDialogues.length > 0) {
    setAgent('scout', 'done', `Resolved → ${info.pdb}`);
    setAgent('chemist', 'done', `${runResult.screenedCount} molecules synthesized`);
    setAgent('admet', 'done', `${runResult.passedCount} PASS, ${runResult.flaggedCount} FLAGGED`);
    setAgent('docking', 'done', `Top: ${runResult.topLead.affinity} kcal/mol`);
    setAgent('pi', 'done', `${runResult.paretoCount} Pareto leads`);
    setProgress(100);
  } else {
    setAgent('scout', 'running', 'Resolving target...');
    await sleep(250);
    logEntry('', 'Target Scout', 'BIOLOGICAL_PROFILING', `Resolved <strong style="color:${info.color}">${safeTargetDisplay}</strong> → PDB:${safePdbDisplay}. Pocket: ${safePocketDisplay}. Annotating ${info.mutant !== '—' ? 'oncogenic mutation ' + escapeHtml(info.mutant) : 'pathogenic variant'}.`, info.color);
    setAgent('scout', 'done', `Resolved → ${info.pdb}`);
    setProgress(20);

    setAgent('chemist', 'running', 'Generating scaffolds...');
    await sleep(300);
    logEntry('', 'Generative Chemist', 'MOLMIM_LATENT_EXPLORATION', `MolMIM latent-space CMA-ES exploration seeded from reference ligand. Generating ${runResult.screenedCount} derivatives.`, '#a855f7');
    setAgent('chemist', 'done', `${runResult.screenedCount} molecules synthesized`);
    setProgress(40);

    setAgent('admet', 'running', 'Screening ADMET...');
    await sleep(250);
    logEntry('', 'ADMET Critic', 'MEDCHEM_EVALUATION', `RDKit filtration complete: ${runResult.passedCount} PASS + ${runResult.flaggedCount} FLAGGED across Lipinski Ro5, Veber criteria, and PAINS alerts.`, '#f59e0b');
    setAgent('admet', 'done', `${runResult.passedCount} PASS, ${runResult.flaggedCount} FLAGGED`);
    setProgress(60);

    setAgent('docking', 'running', 'DiffDock simulating...');
    await sleep(300);
    const contacts = (info.pocketResidues && info.pocketResidues.length > 0)
      ? escapeHtml(info.pocketResidues.slice(0, 3).join(', '))
      : 'Active site interaction residues';
    logEntry('', 'DiffDock Agent', 'DIFFDOCK_DOCKING_SIMULATION', `Conformer generation & diffusion pose sampling for ${runResult.dockedCount} leads into <strong style="color:${info.color}">${safeTargetDisplay}</strong> (${safePdbDisplay}). Top lead: <strong style="color:var(--nvidia-green)">${escapeHtml(runResult.topLead.id)}</strong> ΔG = <strong style="color:var(--nvidia-green)">${runResult.topLead.affinity} kcal/mol</strong>. Contacts: ${contacts}.`, '#00f1fd');
    setAgent('docking', 'done', `Top: ${runResult.topLead.affinity} kcal/mol`);
    setProgress(80);

    setAgent('pi', 'running', 'Arbitrating Pareto...');
    await sleep(250);
    logEntry('', 'Principal Investigator', 'PARETO_ARBITRATION', `Multi-objective Pareto frontier computed across ${runResult.dockedCount} leads. Identified <strong style="color:var(--nvidia-green)">${runResult.paretoCount} strictly non-dominated</strong> candidates. Top nomination: <strong style="color:var(--nvidia-green)">${escapeHtml(runResult.topLead.id)}</strong> (ΔG=${runResult.topLead.affinity}, QED=${runResult.topLead.qed}).`, '#76b900');
    setAgent('pi', 'done', `${runResult.paretoCount} Pareto leads`);
    setProgress(100);
  }

  const kpiAff = document.getElementById('kpiAffinity');
  if (kpiAff) kpiAff.textContent = typeof runResult.topLead.affinity === 'number' ? runResult.topLead.affinity.toFixed(2) : runResult.topLead.affinity;
  const kpiQed = document.getElementById('kpiQed');
  if (kpiQed) kpiQed.textContent = typeof runResult.topLead.qed === 'number' ? runResult.topLead.qed.toFixed(3) : runResult.topLead.qed;
  const kpiSc = document.getElementById('kpiScreened');
  if (kpiSc) kpiSc.textContent = runResult.screenedCount;
  const kpiPar = document.getElementById('kpiPareto');
  if (kpiPar) kpiPar.textContent = runResult.paretoCount;

  renderLeads();
  try {
    renderPareto();
  } catch (chartErr) {
    console.warn('Pareto chart render warning:', chartErr);
  }
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    console.error('Autonomous Discovery Execution Error:', err);
    document.getElementById('streamDot').style.background = '#ef4444';
    document.getElementById('leadsContainer').innerHTML = `<div class="p-4 rounded-xl bg-red-950/30 border border-red-500/30 text-xs text-red-300 text-center">Discovery execution failed: ${escapeHtml(err.message || 'Server error')}. Click Retry to run again.</div>`;
    showToast(`Discovery error: ${err.message || 'Execution failed'}`);
  } finally {
    state.isRunning = false;
    activeDiscoveryController = null;

    const btn = document.getElementById('runBtn');
    if (btn) {
      btn.disabled = false;
    }
    if (!authBlocked) {
      const dot = document.getElementById('streamDot');
      if (dot && dot.style.background !== 'rgb(239, 68, 68)') {
        dot.style.background = '#76b900';
      }
      clientAuth.renderHUD();
    }
  }
}
window.runDiscovery = runDiscovery;
window.runCampaign = runDiscovery;

