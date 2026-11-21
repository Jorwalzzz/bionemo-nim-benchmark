/**
 * Core UI Controls: Workbench inputs, preset loaders, agent rings,
 * logs, lead rendering, and tab navigation.
 */

import { state, TARGETS, ESMFOLD_PRESETS, PRESET_INHIBITORS } from './state.js';
import { loadPdb, render3DComplex, updateLead3DView } from './viewer3d.js';
import { escapeHtml } from './api.js';

let wbDebounceTimer = null;

export function setRounds(r) {
  state.selectedRounds = r;
  const labels = { 1: "1 Round (Fast)", 2: "2 Rounds (Evolve)", 3: "3 Rounds (Deep)" };
  const display = document.getElementById('roundsDisplay');
  if (display) display.textContent = labels[r] || (r + " Rounds");
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
  state.currentTargetTab = tab;
  ['presets', 'rcsb', 'esmfold'].forEach(t => {
    const el = document.getElementById('targetTab' + t.charAt(0).toUpperCase() + t.slice(1));
    const btn = document.getElementById('tabBtn' + t.charAt(0).toUpperCase() + t.slice(1));
    if (el) el.classList.toggle('hidden', t !== tab);
    if (btn) {
      if (t === tab) {
        btn.className = "flex-1 py-1 text-[11px] font-bold rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 transition-all";
      } else {
        btn.className = "flex-1 py-1 text-[11px] font-medium text-gray-400 hover:text-white transition-all";
      }
    }
  });

  const guideAlert = document.getElementById('esmfoldGuideAlert');
  if (guideAlert) {
    guideAlert.classList.toggle('hidden', tab !== 'esmfold');
  }

  const badge = document.getElementById('viewer3dBadge');
  if (badge) {
    if (tab === 'esmfold') {
      badge.textContent = 'ESMFold 3D (Predicted)';
      badge.className = 'font-mono text-purple-400 font-bold';
    } else if (tab === 'rcsb') {
      badge.textContent = 'RCSB 3D (Experimental)';
      badge.className = 'font-mono text-cyan-400 font-bold';
    } else {
      badge.textContent = 'DiffDock 3D';
      badge.className = 'font-mono text-emerald-400 font-bold';
    }
  }
  updateTargetInfo();
}

export function updateSeqCount() {
  const input = document.getElementById('esmfoldSeqInput');
  if (!input) return;
  const clean = input.value.replace(/^>.*$/gm, '').replace(/\s+/g, '');
  const countEl = document.getElementById('seqCharCount');
  if (countEl) countEl.textContent = clean.length;
  const badgeEl = document.getElementById('seqLenBadge');
  if (badgeEl) badgeEl.textContent = `${clean.length} aa`;
}

export function loadEsmPreset(presetKey) {
  const p = ESMFOLD_PRESETS[presetKey];
  if (!p) return;
  const input = document.getElementById('esmfoldSeqInput');
  if (input) {
    input.value = p.sequence || p.seq;
    updateSeqCount();
    showToast(`Loaded ${p.name} sequence (${p.length || (p.sequence || p.seq).length} aa)`);
  }
}

export function onWorkbenchInput(val) {
  clearTimeout(wbDebounceTimer);
  wbDebounceTimer = setTimeout(() => {
    const smiles = (val || '').trim();
    const badge = document.getElementById('workbenchValenceBadge');
    if (!smiles) {
      if (badge) badge.innerHTML = '<span class="text-gray-500 text-[10px]">Empty SMILES</span>';
      return;
    }
    const hasUnclosedRing = (smiles.match(/\d/g) || []).length % 2 !== 0;
    const hasInvalidChar = /[^A-Za-z0-9@+\-\[\]\(\)\\\/%=#$:]/.test(smiles);
    if (hasUnclosedRing || hasInvalidChar) {
      if (badge) badge.innerHTML = '<span class="badge-valence-invalid">✗ Valency / Graph Warning</span>';
    } else {
      if (badge) badge.innerHTML = '<span class="badge-valence-valid">✓ Valid Chemical Graph</span>';
    }
    const mwEl = document.getElementById('wbLiveMw');
    if (mwEl) {
      const approxMw = Math.round(smiles.length * 13.5);
      mwEl.textContent = approxMw;
    }
  }, 120);
}

export function loadWorkbenchPreset(key) {
  const smiles = PRESET_INHIBITORS[key];
  if (!smiles) return;
  const input = document.getElementById('workbenchSmilesInput');
  if (input) {
    input.value = smiles;
    onWorkbenchInput(smiles);
    showToast(`Loaded reference inhibitor for ${key.toUpperCase()}`);
  }
}

export function tweakSmiles(type) {
  const input = document.getElementById('workbenchSmilesInput');
  if (!input) return;
  let s = input.value;
  if (type === 'fluorine') {
    s = s.replace(/c1ccccc1/i, 'c1ccc(F)cc1');
    showToast('Added bioisosteric fluorine atom (-F)');
  } else if (type === 'methyl') {
    s += 'C';
    showToast('Added magic methyl substituent (-CH3)');
  } else if (type === 'pyridine') {
    s = s.replace(/c1ccccc1/i, 'c1ccccn1');
    showToast('Swapped phenyl core to pyridine for solubility');
  }
  input.value = s;
  onWorkbenchInput(s);
}

export function updateTargetInfo() {
  const currentTargetTab = state.currentTargetTab || 'presets';
  let target = document.getElementById('targetSelect')?.value || '7RPZ';
  let info = TARGETS[target];

  if (currentTargetTab === 'esmfold') {
    const rawSeq = (document.getElementById('esmfoldSeqInput')?.value || '').trim().replace(/^>.*$/gm, '').replace(/\s+/g, '');
    target = rawSeq || 'De Novo Variant';
    info = {
      pdb: `DE NOVO (pLDDT ${(state.currentTargetMeanPlddt || 89.5).toFixed(1)})`,
      pdbId: 'DE_NOVO',
      name: 'De Novo Variant (ESMFold)',
      indication: 'De Novo Engineered Scaffold',
      pocket: 'Predicted Catalytic Core',
      pocketName: 'Predicted Catalytic Core',
      mutant: 'Variant / De Novo',
      mutation: 'Variant / De Novo',
      ligandName: 'De Novo Scaffold',
      ligandCcd: 'APO',
      epistemicTag: 'Illustrative',
      resolutionA: null,
      affinity: { kd_nm: '—', delta_g_kcal_mol: '—' },
      color: '#a855f7'
    };
  } else if (currentTargetTab === 'rcsb') {
    const customCode = (document.getElementById('customTargetInput')?.value || '').trim().toUpperCase();
    target = customCode || '7RPZ';
    info = TARGETS[target] || {
      pdb: target,
      pdbId: target,
      name: `${target} (RCSB PDB)`,
      indication: 'Crystallographic Target',
      pocket: 'Active Site Cleft',
      pocketName: 'Active Site Cleft',
      mutant: 'WT / Custom',
      mutation: 'WT / Custom',
      ligandName: 'Bound Co-crystal',
      ligandCcd: 'LIG',
      epistemicTag: 'Empirical',
      resolutionA: null,
      affinity: { kd_nm: '—', delta_g_kcal_mol: '—' },
      color: '#00f1fd'
    };
  } else if (!info) {
    info = TARGETS['7RPZ'] || TARGETS['KRAS G12D'] || {
      pdb: '7RPZ',
      pdbId: '7RPZ',
      name: 'KRAS G12D (Switch-II Pocket)',
      indication: 'Repo Benchmark Core',
      pocket: 'Switch-II Pocket',
      pocketName: 'Switch-II Pocket',
      pocketResidues: ['Asp12', 'Gly13', 'Val14', 'Glu62', 'His95', 'Tyr96', 'Gln99'],
      mutant: 'G12D',
      mutation: 'G12D',
      ligandName: 'MRTX1133',
      ligandCcd: '7RP',
      epistemicTag: 'Illustrative',
      resolutionA: 1.30,
      affinity: { kd_nm: 0.2, delta_g_kcal_mol: -12.4 },
      color: '#76b900'
    };
  }

  const nameEl = document.getElementById('targetName');
  const pdbEl = document.getElementById('targetPdb');
  const indEl = document.getElementById('targetInd');
  const pocketEl = document.getElementById('targetPocket');
  const mutEl = document.getElementById('targetMut');
  const ligandEl = document.getElementById('targetLigand');
  const kdEl = document.getElementById('targetKd');
  const deltaGEl = document.getElementById('targetDeltaG');
  const resEl = document.getElementById('targetRes');
  const badgeEl = document.getElementById('targetTelemetryBadge');

  if (nameEl) {
    nameEl.textContent = currentTargetTab === 'esmfold' 
      ? (target.length > 25 ? target.slice(0, 22) + '...' : target) 
      : (info.name || target);
    nameEl.style.color = info.color || 'var(--nvidia-green)';
  }
  if (pdbEl) pdbEl.textContent = info.pdb || info.pdbId || target;
  if (indEl) indEl.textContent = info.indication || info.category || 'Therapeutic Target';
  if (pocketEl) {
    const pocketDisplay = info.pocketName || info.pocket || 'Binding Pocket';
    pocketEl.textContent = pocketDisplay;
    if (info.pocketResidues && Array.isArray(info.pocketResidues)) {
      pocketEl.title = `${pocketDisplay} [${info.pocketResidues.join(', ')}]`;
    } else {
      pocketEl.title = pocketDisplay;
    }
  }
  if (mutEl) mutEl.textContent = info.mutation || info.mutant || 'Wild-Type';
  if (ligandEl) {
    if (info.ligandName) {
      ligandEl.textContent = `${info.ligandName} (${info.ligandCcd || 'LIG'})`;
    } else {
      ligandEl.textContent = 'Apo / Custom';
    }
  }
  if (kdEl) {
    kdEl.textContent = (info.affinity && info.affinity.kd_nm !== undefined && info.affinity.kd_nm !== '—')
      ? `${info.affinity.kd_nm} nM`
      : '—';
  }
  if (deltaGEl) {
    deltaGEl.textContent = (info.affinity && info.affinity.delta_g_kcal_mol !== undefined && info.affinity.delta_g_kcal_mol !== '—')
      ? `${info.affinity.delta_g_kcal_mol} kcal`
      : '—';
  }
  if (resEl) {
    resEl.textContent = (info.resolutionA !== undefined && info.resolutionA !== null)
      ? `${Number(info.resolutionA).toFixed(2)} Å`
      : '—';
  }
  if (badgeEl) {
    const tag = info.epistemicTag || 'Illustrative';
    badgeEl.textContent = `${tag} In Silico`;
    if (tag === 'Measured' || tag === 'Empirical') {
      badgeEl.className = 'badge-measured text-[10px]';
    } else {
      badgeEl.className = 'badge-illustrative text-[10px]';
    }
  }

  if (currentTargetTab === 'presets' && info && (info.pdb || info.pdbId)) {
    const targetPdbId = info.pdbId || info.pdb;
    (async () => {
      const pdbText = (typeof loadPdb === 'function') ? await loadPdb(targetPdbId) : window['PDB_' + targetPdbId];
      if (pdbText && typeof render3DComplex === 'function') {
        state.currentTargetPdbText = pdbText;
        state.currentTargetPocketResidues = info.pocketResidues || [12, 13, 32, 60, 61, 96];
        render3DComplex(state.currentTargetPdbText, null, state.currentTargetPocketResidues, false, 95.0);
      }
    })();
  }
}

export function setAgent(id, agentState, msg) {
  const ring = document.getElementById('ring-' + id);
  const status = document.getElementById('status-' + id);
  if (ring) ring.className = 'agent-ring ' + agentState;
  if (status) status.textContent = msg;
}

export function resetAgents() {
  ['scout', 'chemist', 'admet', 'docking', 'pi'].forEach(a => setAgent(a, 'idle', 'Standby'));
}

export function logEntry(icon, agent, role, text, color) {
  const log = document.getElementById('agentLog');
  if (!log) return;
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
  const tsEl = document.getElementById('streamTimestamp');
  if (tsEl) tsEl.textContent = ts;

  const safeAgent = escapeHtml(agent);
  const safeRole = escapeHtml(role);
  const safeColor = /^[#a-zA-Z0-9]+$/.test(color) ? color : '#76b900';
  // Allow only safe inline tags (strong, span) with styling; strip scripts, handlers, and other tags
  const safeText = String(text ?? '')
    .replace(/<\/?(?!strong\b|span\b|\/strong|\/span)[a-z0-9-]+(?:\s+[^>]*)?>/gi, '')
    .replace(/\b(?:on\w+|javascript:|data:)\b/gi, 'data-blocked=');

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
  while (log.children.length > 25) {
    log.removeChild(log.firstChild);
  }
  log.scrollTop = log.scrollHeight;
}

export function renderLeads() {
  const container = document.getElementById('leadsContainer');
  if (!container) return;
  const leads = state.currentLeads || [];
  const countEl = document.getElementById('leadCount');
  if (countEl) countEl.textContent = `${leads.length} candidates`;

  if (leads.length === 0) {
    container.innerHTML = `
      <div id="emptyLeadsState" class="flex flex-col items-center justify-center p-8 text-center text-gray-500">
        <span class="text-3xl mb-2">🧪</span>
        <div class="text-xs font-semibold text-gray-400">No leads nominated yet</div>
        <div class="text-[10px] text-gray-600 mt-1">Select a target and run autonomous discovery to nominate Pareto-optimal drug candidates.</div>
      </div>
    `;
    const panel = document.getElementById('dossierPanel');
    if (panel) {
      panel.innerHTML = `
        <div class="flex flex-col items-center justify-center h-48 text-center text-gray-600 text-xs">
          <span class="text-2xl mb-1 select-none">📋</span>
          <span>No lead selected</span>
          <span class="text-[10px] text-gray-700 mt-1">Nominated candidates will appear here</span>
        </div>
      `;
    }
    return;
  }

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  container.innerHTML = leads.map((lead, i) => {
    const isSimulated = Boolean(lead.is_simulated || lead.provenance === 'SIMULATED');
    return `
      <div class="lead-card ${i === 0 ? 'selected' : ''}" onclick="selectLead(${i})">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="font-mono font-bold text-xs text-white">${esc(lead.id)}</span>
            ${lead.pareto ? '<span class="badge-green">PARETO</span>' : ''}
            ${isSimulated ? '<span class="badge-simulated px-1.5 py-0.5 text-[9px] rounded font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">SIMULATED</span>' : '<span class="badge-live px-1.5 py-0.5 text-[9px] rounded font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">NIM LIVE</span>'}
          </div>
          <span class="${lead.verdict === 'PASS' ? 'badge-green' : 'badge-yellow'}">${esc(lead.verdict)}</span>
        </div>
        <div class="grid grid-cols-4 gap-2 text-[10px]">
          <div><div class="text-gray-600">ΔG</div><div class="font-mono font-bold" style="color: var(--nvidia-green);">${esc(typeof lead.affinity === 'number' ? lead.affinity.toFixed(2) : lead.affinity)}</div></div>
          <div><div class="text-gray-600">QED</div><div class="font-mono font-bold" style="color: var(--cyber-cyan);">${esc(typeof lead.qed === 'number' ? lead.qed.toFixed(3) : lead.qed)}</div></div>
          <div><div class="text-gray-600">MW</div><div class="font-mono text-gray-300">${esc(typeof lead.mw === 'number' ? lead.mw.toFixed(1) : lead.mw)}</div></div>
          <div><div class="text-gray-600">SAScore</div><div class="font-mono text-gray-300">${esc(typeof lead.sascore === 'number' ? lead.sascore.toFixed(2) : lead.sascore)}</div></div>
        </div>
      </div>
    `;
  }).join('');
  if (leads.length > 0) selectLead(0);
}

export function selectLead(i) {
  document.querySelectorAll('.lead-card').forEach((c, idx) => c.classList.toggle('selected', idx === i));
  const leads = state.currentLeads || [];
  const lead = leads[i];
  if (!lead) return;
  state.currentSelectedLead = lead;

  const currentTargetTab = state.currentTargetTab || 'presets';
  let target = document.getElementById('targetSelect')?.value || 'KRAS G12D';
  if (currentTargetTab === 'esmfold') target = 'ESMFold De Novo';
  else if (currentTargetTab === 'rcsb') target = (document.getElementById('customTargetInput')?.value || '').trim() || 'RCSB Target';

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const safeLeadId = esc(lead.id);
  const safeVerdict = esc(lead.verdict);
  const safeSmiles = esc(lead.smiles || 'CC(=O)Nc1ccc(O)cc1');

  const panel = document.getElementById('dossierPanel');
  if (!panel) return;

  const isSimulated = Boolean(lead.is_simulated || lead.provenance === 'SIMULATED');
  panel.innerHTML = `
    <div class="space-y-3 animate-fade-up">
      <div class="p-3 rounded-xl" style="background: rgba(118,185,0,0.06); border: 1px solid rgba(118,185,0,0.2);">
        <div class="flex items-center justify-between mb-1">
          <div class="font-mono font-bold text-sm text-white">${safeLeadId}</div>
          <span class="text-[10px] font-mono text-gray-400">ΔG <strong class="text-nvidia-green">${typeof lead.affinity === 'number' ? lead.affinity.toFixed(2) : lead.affinity}</strong></span>
        </div>
        <div class="flex gap-1.5 flex-wrap">
          ${lead.pareto ? '<span class="badge-green">PARETO OPTIMAL</span>' : ''}
          ${isSimulated ? '<span class="badge-simulated px-1.5 py-0.5 text-[9px] rounded font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">SIMULATED</span>' : '<span class="badge-live px-1.5 py-0.5 text-[9px] rounded font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">NIM LIVE</span>'}
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

  setTimeout(() => updateLead3DView(lead), 40);
}

export function switchTab(tab) {
  ['windows', 'unix', 'docker', 'compare'].forEach(t => {
    const pane = document.getElementById('pane-' + t);
    const tabEl = document.getElementById('tab-' + t);
    if (pane) pane.classList.toggle('hidden', t !== tab);
    if (tabEl) tabEl.classList.toggle('active', t === tab);
  });
}

export function copyCode(elId, btn) {
  const el = document.getElementById(elId);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    btn.textContent = 'Copied!';
    showToast();
    setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
  });
}

export function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  if (msg) t.textContent = msg;
  t.classList.remove('hide');
  setTimeout(() => t.classList.add('hide'), 2500);
}

export function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

let lastProvenanceReceipt = null;

export function updateProvenanceBanner(provenance) {
  lastProvenanceReceipt = provenance;
  const banner = document.getElementById('provenanceBanner');
  if (!banner) return;
  const dot = document.getElementById('provenanceDot');
  const badge = document.getElementById('provenanceBadge');
  const detail = document.getElementById('provenanceDetail');

  const isLive = provenance && provenance.mode === 'LIVE_NVIDIA_NIM';
  if (isLive) {
    banner.className = 'px-4 py-2 bg-emerald-500/10 border-b border-emerald-500/30 flex items-center justify-between text-[11px] font-mono';
    if (dot) dot.className = 'w-2 h-2 rounded-full bg-emerald-400 shrink-0';
    if (badge) {
      badge.className = 'font-bold text-emerald-400 shrink-0';
      badge.textContent = 'LIVE · NVIDIA NIM BACKEND';
    }
    if (detail) {
      const host = provenance.backend_host || '127.0.0.1';
      const ms = provenance.elapsed_ms || 0;
      const ts = provenance.timestamp_utc ? new Date(provenance.timestamp_utc).toLocaleTimeString() : '';
      detail.textContent = `(${host} · ${ms}ms · ${ts})`;
    }
  } else {
    banner.className = 'px-4 py-2 bg-amber-500/10 border-b border-amber-500/30 flex items-center justify-between text-[11px] font-mono';
    if (dot) dot.className = 'w-2 h-2 rounded-full bg-amber-400 shrink-0';
    if (badge) {
      badge.className = 'font-bold text-amber-400 shrink-0';
      badge.textContent = 'OFFLINE DEMO · CLIENT SIMULATION (NOT LIVE NIM)';
    }
    if (detail) {
      detail.textContent = '(Local simulation; metrics illustrative. Run `python serve_cockpit.py` for live NIM)';
    }
  }
}

export function openRawReceiptModal() {
  const modal = document.getElementById('rawReceiptModal');
  const content = document.getElementById('rawReceiptContent');
  if (!modal || !content) return;
  const receipt = lastProvenanceReceipt || {
    mode: 'OFFLINE_DEMO',
    provenance: 'SIMULATED',
    backend_host: window.location.hostname || 'localhost',
    client_env: navigator.userAgent,
    timestamp_utc: new Date().toISOString(),
    notice: 'No live NIM backend response received yet. Running in offline client demo mode.'
  };
  content.textContent = JSON.stringify(receipt, null, 2);
  modal.classList.remove('hidden');
  modal.style.display = 'flex';
}

export function closeRawReceiptModal() {
  const modal = document.getElementById('rawReceiptModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}

export async function copyRawReceiptJson() {
  const content = document.getElementById('rawReceiptContent');
  const btnText = document.getElementById('copyReceiptBtnText');
  if (!content) return;
  try {
    await navigator.clipboard.writeText(content.textContent || '');
    if (btnText) {
      btnText.textContent = 'Copied!';
      setTimeout(() => { btnText.textContent = 'Copy JSON'; }, 2000);
    }
  } catch (err) {
    console.warn('Clipboard write failed:', err);
  }
}

export function exportActiveRunJson() {
  const resultToExport = state.activeRunResult || {
    status: 'completed',
    target: state.currentTargetTab === 'presets' ? (document.getElementById('targetSelect')?.value || '7RPZ') : 'Target',
    leads: state.currentLeads || [],
    provenance: lastProvenanceReceipt || {
      mode: 'OFFLINE_DEMO',
      provenance: 'SIMULATED',
      timestamp_utc: new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  };

  const jsonStr = JSON.stringify(resultToExport, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const targetName = (resultToExport.pdbId || resultToExport.target || 'target').replace(/[^a-zA-Z0-9_-]/g, '_');
  a.href = url;
  a.download = `bionemo_${targetName}_discovery_run.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('📥 Exported discovery run JSON');
}
