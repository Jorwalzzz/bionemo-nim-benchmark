/**
 * BioNeMo NIM Inference Benchmark - Two-Pane CLI Reproducibility Builder
 * Module: ./js/cli-builder.js
 * 
 * Implements:
 * 1. Two-pane reactive CLI flag builder (endpoint, target, poses, batch-size, format, mock).
 * 2. Real-time syntax-colored terminal command preview.
 * 3. Tactile quick preset configurations (Mock Dry-Run, KRAS Screening, Full Suite).
 * 4. Animated one-click command copy with clipboard verification.
 */

(function () {
  'use strict';

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  const state = {
    endpoint: 'health.api.nvidia.com',
    target: '7RPZ',
    poses: 5,
    admetFilter: true,
    batchSize: 32,
    outputFormat: 'json',
    mock: true
  };

  // DOM Elements cache
  let selectEndpoint = null;
  let selectTarget = null;
  let rangePoses = null;
  let displayPoses = null;
  let toggleAdmet = null;
  let selectBatch = null;
  let selectFormat = null;
  let toggleMock = null;
  let terminalCodeEl = null;
  let btnCopy = null;
  let presetBtns = [];

  function generateRawCommand() {
    let cmd = `python run_benchmark.py \\\n  --endpoint "${state.endpoint}" \\\n  --target ${state.target} \\\n  --poses ${state.poses} \\\n  --batch-size ${state.batchSize} \\\n  --output-format ${state.outputFormat}`;

    if (state.admetFilter) {
      cmd += ` \\\n  --admet-filter`;
    }
    if (state.mock) {
      cmd += ` \\\n  --mock`;
    }

    return cmd;
  }

  function updateTerminalView() {
    if (!terminalCodeEl) return;

    let html = `<span class="cmd-bin">python run_benchmark.py</span> \\\n`;
    html += `  <span class="cmd-flag">--endpoint</span> <span class="cmd-val">"${escapeHtml(state.endpoint)}"</span> \\\n`;
    html += `  <span class="cmd-flag">--target</span> <span class="cmd-val">${escapeHtml(state.target)}</span> \\\n`;
    html += `  <span class="cmd-flag">--poses</span> <span class="cmd-val">${escapeHtml(state.poses)}</span> \\\n`;
    html += `  <span class="cmd-flag">--batch-size</span> <span class="cmd-val">${escapeHtml(state.batchSize)}</span> \\\n`;
    html += `  <span class="cmd-flag">--output-format</span> <span class="cmd-val">${escapeHtml(state.outputFormat)}</span>`;

    if (state.admetFilter) {
      html += ` \\\n  <span class="cmd-flag">--admet-filter</span>`;
    }
    if (state.mock) {
      html += ` \\\n  <span class="cmd-flag">--mock</span>`;
    }

    terminalCodeEl.innerHTML = html;
  }

  function applyPreset(presetKey) {
    if (presetKey === 'mock') {
      state.endpoint = 'health.api.nvidia.com';
      state.target = '7RPZ';
      state.poses = 5;
      state.admetFilter = true;
      state.batchSize = 16;
      state.outputFormat = 'json';
      state.mock = true;
    } else if (presetKey === 'kras') {
      state.endpoint = 'health.api.nvidia.com';
      state.target = '7RPZ';
      state.poses = 10;
      state.admetFilter = true;
      state.batchSize = 32;
      state.outputFormat = 'pdf';
      state.mock = false;
    } else if (presetKey === 'full') {
      state.endpoint = 'localhost:8000';
      state.target = 'ALL_TARGETS';
      state.poses = 5;
      state.admetFilter = true;
      state.batchSize = 64;
      state.outputFormat = 'csv';
      state.mock = true;
    }

    // Sync input controls with new state
    if (selectEndpoint) selectEndpoint.value = state.endpoint;
    if (selectTarget) selectTarget.value = state.target;
    if (rangePoses) rangePoses.value = state.poses;
    if (displayPoses) displayPoses.textContent = `${state.poses} Poses`;
    if (toggleAdmet) toggleAdmet.checked = state.admetFilter;
    if (selectBatch) selectBatch.value = state.batchSize;
    if (selectFormat) selectFormat.value = state.outputFormat;
    if (toggleMock) toggleMock.checked = state.mock;

    updateTerminalView();
  }

  function init() {
    selectEndpoint = document.getElementById('cli-endpoint');
    selectTarget = document.getElementById('cli-target');
    rangePoses = document.getElementById('cli-poses');
    displayPoses = document.getElementById('cli-poses-display');
    toggleAdmet = document.getElementById('cli-admet');
    selectBatch = document.getElementById('cli-batch');
    selectFormat = document.getElementById('cli-format');
    toggleMock = document.getElementById('cli-mock');
    terminalCodeEl = document.getElementById('cli-terminal-code');
    btnCopy = document.getElementById('btn-copy-cli-command');
    presetBtns = Array.from(document.querySelectorAll('.cli-preset-btn'));

    // Input listeners
    if (selectEndpoint) {
      selectEndpoint.addEventListener('change', (e) => {
        state.endpoint = e.target.value;
        updateTerminalView();
      });
    }
    if (selectTarget) {
      selectTarget.addEventListener('change', (e) => {
        state.target = e.target.value;
        updateTerminalView();
      });
    }
    if (rangePoses) {
      rangePoses.addEventListener('input', (e) => {
        state.poses = parseInt(e.target.value, 10);
        if (displayPoses) displayPoses.textContent = `${state.poses} Poses`;
        updateTerminalView();
      });
    }
    if (toggleAdmet) {
      toggleAdmet.addEventListener('change', (e) => {
        state.admetFilter = e.target.checked;
        updateTerminalView();
      });
    }
    if (selectBatch) {
      selectBatch.addEventListener('change', (e) => {
        state.batchSize = parseInt(e.target.value, 10);
        updateTerminalView();
      });
    }
    if (selectFormat) {
      selectFormat.addEventListener('change', (e) => {
        state.outputFormat = e.target.value;
        updateTerminalView();
      });
    }
    if (toggleMock) {
      toggleMock.addEventListener('change', (e) => {
        state.mock = e.target.checked;
        updateTerminalView();
      });
    }

    // Presets listeners
    presetBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        presetBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const p = btn.getAttribute('data-preset');
        applyPreset(p);
      });
    });

    // Copy Button
    if (btnCopy) {
      btnCopy.addEventListener('click', () => {
        const raw = generateRawCommand();
        navigator.clipboard.writeText(raw).then(() => {
          const original = btnCopy.innerHTML;
          btnCopy.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
            <span>Command Copied!</span>
          `;
          setTimeout(() => {
            btnCopy.innerHTML = original;
          }, 2000);
        });
      });
    }

    // Initial render
    updateTerminalView();
  }

  // Bind to DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.BioNeMoCLI = {
    getState: () => ({ ...state }),
    applyPreset
  };
})();
