/**
 * Shared DOM, Export, Clipboard, Network Health, Modal Dialog & Popover Toast Utilities
 * Clean ES module imported by both welcome-page scripts (./js/*.js) and cockpit modules (./js/cockpit/*.js).
 */

export function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Neutralizes spreadsheet formula injection (CWE-1236) and wraps per RFC 4180.
 */
export function toCsvCell(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '';
  const str = String(value);
  if (/^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(str.trim())) return str.trim();
  const neutralized = /^\s*[=+\-@\t\r]/.test(str) ? `'${str}` : str;
  return /[",\n\r]/.test(neutralized) ? `"${neutralized.replace(/"/g, '""')}"` : neutralized;
}

export function downloadBlob(content, filename, mimeType = 'text/plain;charset=utf-8;') {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function copyToClipboard(text) {
  const payload = String(text ?? '');
  if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(payload);
      return true;
    } catch (_) {
      // Fallback below
    }
  }
  try {
    const ta = document.createElement('textarea');
    ta.value = payload;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return Boolean(ok);
  } catch (_) {
    return false;
  }
}

let _cachedBackendUp = null;
let _cachedBackendHealth = null;
let _probePromise = null;

export function getCachedBackendHealth() {
  return _cachedBackendHealth;
}

export function isStaticDeploymentOrigin() {
  if (typeof window === 'undefined') return true;
  const proto = window.location.protocol;
  const host = window.location.hostname || '';
  const overrideLocal =
    typeof window.location.search === 'string' &&
    new URLSearchParams(window.location.search).get('backend') === 'local';
  if (overrideLocal) return false;
  return (
    proto === 'file:' ||
    host.endsWith('github.io') ||
    host.endsWith('pages.dev') ||
    !proto.startsWith('http')
  );
}

/**
 * Probes FastAPI availability cleanly without emitting 404 console errors on static servers.
 */
export async function probeBackendHealth(timeoutMs = 1500, force = false) {
  if (isStaticDeploymentOrigin()) {
    _cachedBackendUp = false;
    _cachedBackendHealth = null;
    return false;
  }
  if (!force && _cachedBackendUp !== null) {
    return _cachedBackendUp;
  }
  if (_probePromise) {
    return _probePromise;
  }

  _probePromise = (async () => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const headRes = await fetch('./cockpit.html', {
        method: 'HEAD',
        signal: controller.signal
      });
      if ((headRes.headers.get('X-BioNeMo-Backend') || '').toLowerCase() !== 'fastapi') {
        _cachedBackendUp = false;
        _cachedBackendHealth = null;
        return false;
      }
      const res = await fetch('./api/health', {
        method: 'GET',
        headers: { Accept: 'application/json' },
        signal: controller.signal
      });
      if (!res.ok) {
        _cachedBackendUp = false;
        _cachedBackendHealth = null;
        return false;
      }
      const data = await res.json();
      _cachedBackendHealth = data;
      _cachedBackendUp = Boolean(data && data.status && data.status !== 'error');
      return _cachedBackendUp;
    } catch (_) {
      _cachedBackendUp = false;
      _cachedBackendHealth = null;
      return false;
    } finally {
      clearTimeout(timer);
      _probePromise = null;
    }
  })();

  return _probePromise;
}

export function openModalDialog(dialogEl, { nonModal = false } = {}) {
  if (!dialogEl) return;
  dialogEl.classList.remove('hidden');
  dialogEl.style.removeProperty('display');
  if (typeof dialogEl.showModal === 'function' && !nonModal) {
    if (!dialogEl.open) {
      dialogEl.showModal();
    }
    return;
  }
  if (typeof dialogEl.show === 'function' && nonModal) {
    if (!dialogEl.open) {
      dialogEl.show();
    }
    return;
  }
  dialogEl.style.display = 'flex';
}

export function closeModalDialog(dialogEl) {
  if (!dialogEl) return;
  if (typeof dialogEl.close === 'function') {
    if (dialogEl.open) {
      dialogEl.close();
    }
    return;
  }
  dialogEl.style.display = 'none';
  dialogEl.classList.add('hidden');
}

let _toastTimer = null;

export function showPopoverToast(toastEl, message, durationMs = 3200) {
  if (!toastEl) return;
  toastEl.textContent = String(message ?? '');
  toastEl.classList.remove('hide');

  if (typeof toastEl.showPopover === 'function' && toastEl.hasAttribute('popover')) {
    try {
      if (toastEl.matches(':popover-open')) {
        toastEl.hidePopover();
      }
      toastEl.showPopover();
    } catch (_) {
      toastEl.style.display = 'block';
    }
  } else {
    toastEl.style.display = 'block';
  }

  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => {
    toastEl.classList.add('hide');
    if (typeof toastEl.hidePopover === 'function' && toastEl.hasAttribute('popover')) {
      try {
        if (toastEl.matches(':popover-open')) {
          toastEl.hidePopover();
        }
      } catch (_) {}
    }
  }, durationMs);
}
