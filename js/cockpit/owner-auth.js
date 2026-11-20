/**
 * Agentic BioNeMo - Workstation Owner Access Controller (Localhost Only)
 * 
 * Strict Invariants:
 * - Dormant on remote origins (GitHub Pages / jorwalzzz.github.io).
 * - Safe DOM updates via textContent and element construction only.
 * - Hardware MachineGuid and loopback gated via FastAPI /api/owner endpoints.
 */

import { showToast } from './ui-controls.js';
import { isLocalServer, isStaticHost } from './state.js';

let isOwnerActive = false;

export function isOwner() {
  return isOwnerActive;
}

export function openOwnerModal() {
  if (isStaticHost || !isLocalServer) return;
  const modal = document.getElementById('ownerModal');
  if (!modal) return;
  modal.style.display = 'flex';
  modal.classList.remove('hidden');
  const msg = document.getElementById('ownerStatusMessage');
  if (msg) {
    msg.style.display = 'none';
    msg.classList.add('hidden');
    msg.textContent = '';
  }
  const idInput = document.getElementById('ownerIdInput');
  if (idInput) {
    setTimeout(() => idInput.focus(), 50);
  }
}

export function closeOwnerModal() {
  const modal = document.getElementById('ownerModal');
  if (!modal) return;
  modal.style.display = 'none';
  modal.classList.add('hidden');
}

export async function submitOwnerLogin() {
  const idInput = document.getElementById('ownerIdInput');
  const pwdInput = document.getElementById('ownerPasswordInput');
  const msg = document.getElementById('ownerStatusMessage');
  const submitBtn = document.getElementById('ownerLoginBtn');

  if (!idInput || !pwdInput) return;
  const ownerId = idInput.value.trim();
  const password = pwdInput.value;

  if (!ownerId || !password) {
    if (msg) {
      msg.textContent = 'Please enter both Owner ID and Password.';
      msg.className = 'text-xs px-3 py-2 rounded font-mono bg-red-500/15 text-red-300 border border-red-500/30';
      msg.style.display = 'block';
      msg.classList.remove('hidden');
    }
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Verifying...';
  }

  try {
    const res = await fetch('/api/owner/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ owner_id: ownerId, password: password })
    });

    const data = await res.json().catch(() => ({}));
    if (res.ok && data.success) {
      isOwnerActive = true;
      window.isOwner = true;
      closeOwnerModal();
      pwdInput.value = '';
      showToast('⚡ Owner Verified: Unlimited Discovery & Benchmarks Activated');
      renderOwnerHUD(data.owner_id);
      if (window.clientAuth) {
        window.clientAuth.init();
      }
    } else {
      if (msg) {
        msg.textContent = data.message || 'Authentication failed. Please verify credentials.';
        msg.className = 'text-xs px-3 py-2 rounded font-mono bg-red-500/15 text-red-300 border border-red-500/30';
        msg.style.display = 'block';
        msg.classList.remove('hidden');
      }
    }
  } catch (err) {
    if (msg) {
      msg.textContent = 'Network or endpoint error connecting to owner gate.';
      msg.className = 'text-xs px-3 py-2 rounded font-mono bg-red-500/15 text-red-300 border border-red-500/30';
      msg.style.display = 'block';
      msg.classList.remove('hidden');
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Authenticate';
    }
  }
}

export async function handleOwnerLogout() {
  try {
    const res = await fetch('/api/owner/logout', { method: 'POST' });
    if (res.ok) {
      isOwnerActive = false;
      window.isOwner = false;
      showToast('Owner session logged out.');
      renderOwnerHUD(null);
      if (window.clientAuth) {
        window.clientAuth.init();
      }
    }
  } catch (e) {
    console.error('Owner logout error:', e);
  }
}

export function renderOwnerHUD(ownerId) {
  const container = document.getElementById('ownerAccessContainer');
  if (!container) return;

  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  if (isOwnerActive) {
    container.className = 'flex items-center gap-2';
    container.style.display = 'flex';
    container.classList.remove('hidden');

    const badge = document.createElement('div');
    badge.className = 'flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-xs font-mono font-bold shadow-sm';
    
    const dot = document.createElement('span');
    dot.className = 'w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse';
    badge.appendChild(dot);

    const label = document.createElement('span');
    label.textContent = 'OWNER · UNLIMITED';
    badge.appendChild(label);
    container.appendChild(badge);

    const logoutBtn = document.createElement('button');
    logoutBtn.type = 'button';
    logoutBtn.title = 'Logout Owner Session';
    logoutBtn.onclick = handleOwnerLogout;
    logoutBtn.className = 'px-2 py-1 rounded-lg text-xs font-semibold text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-colors';
    logoutBtn.textContent = '✕';
    container.appendChild(logoutBtn);

    const trialText = document.getElementById('trialText');
    if (trialText) {
      trialText.textContent = '⚡ Owner Workstation Mode • Unlimited Discovery Active';
    }
    const banner = document.getElementById('authRequiredBanner');
    if (banner) {
      banner.style.display = 'none';
      banner.classList.add('hidden');
    }
  } else {
    container.className = 'flex items-center gap-2';
    container.style.display = 'flex';
    container.classList.remove('hidden');

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'ownerAccessBtn';
    btn.onclick = openOwnerModal;
    btn.className = 'px-2.5 py-1.5 rounded-lg text-xs font-mono font-semibold text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 flex items-center gap-1.5 transition-all';
    btn.textContent = '🔒 Owner Access';
    container.appendChild(btn);
  }
}

export async function initOwnerAccess() {
  if (isStaticHost || !isLocalServer) {
    const container = document.getElementById('ownerAccessContainer');
    if (container) {
      container.style.display = 'none';
      container.classList.add('hidden');
    }
    return;
  }

  try {
    const res = await fetch('/api/owner/status');
    if (!res.ok) return;
    const data = await res.json();
    if (data.configured) {
      if (data.authenticated) {
        isOwnerActive = true;
        window.isOwner = true;
        renderOwnerHUD(data.owner_id);
      } else {
        isOwnerActive = false;
        window.isOwner = false;
        renderOwnerHUD(null);
      }
    }
  } catch (e) {
    console.debug('Local owner gate check skipped:', e);
  }
}
