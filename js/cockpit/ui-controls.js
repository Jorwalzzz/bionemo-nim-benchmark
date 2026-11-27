/**
 * Core UI Controls: Workbench inputs, preset loaders, agent rings,
 * logs, lead rendering, and tab navigation.
 */

import { state, probeBackendHealth, TARGETS, ESMFOLD_PRESETS, PRESET_INHIBITORS } from './state.js';
import { loadPdb, render3DComplex, updateLead3DView, evaluateClientRedock } from './viewer3d.js';
import { renderPareto } from './charts.js';
import { escapeHtml } from './api.js';
import {
  copyToClipboard,
  downloadBlob,
  buildExportFilename,
  openModalDialog,
  closeModalDialog,
  showPopoverToast
} from '../shared/dom-utils.js';
import { buildExportContext } from './exports.js';

let wbDebounceTimer = null;
let wbSvgDebounceTimer = null;
let wbSvgAbortController = null;

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
    const metrics = evaluateClientRedock(smiles);
    const mwEl = document.getElementById('wbLiveMw');
    if (mwEl) mwEl.textContent = metrics.mw ? metrics.mw.toFixed(1) : '—';
    const affEl = document.getElementById('wbLiveAffinity');
    if (affEl) affEl.textContent = `${metrics.binding_affinity_kcal_mol.toFixed(2)} kcal/mol`;
    const qedEl = document.getElementById('wbLiveQed');
    if (qedEl) qedEl.textContent = metrics.qed.toFixed(3);
    const sasEl = document.getElementById('wbLiveSas');
    if (sasEl) sasEl.textContent = metrics.sascore.toFixed(2);
  }, 120);

  clearTimeout(wbSvgDebounceTimer);
  wbSvgDebounceTimer = setTimeout(() => {
    updateWorkbench2dPreview((val || '').trim());
  }, 250);
}

export async function updateWorkbench2dPreview(smiles) {
  const imgEl = document.getElementById('wb2dPreviewImg');
  const metaEl = document.getElementById('wb2dPreviewMeta');
  if (!imgEl || !metaEl) return;

  const clean = (smiles || '').trim();
  if (!clean) {
    imgEl.classList.add('hidden');
    metaEl.textContent = 'Enter a SMILES string for 2D preview.';
    return;
  }

  const heteroCount = (clean.match(/[NOSPFClBrI]/gi) || []).length;
  const ringMarkers = Math.floor((clean.match(/\d/g) || []).length / 2);
  const staticSummary = `${clean.length} chars · ~${ringMarkers} ring(s) · ${heteroCount} heteroatom token(s) · 2D SVG requires local backend`;

  if (wbSvgAbortController) {
    wbSvgAbortController.abort();
    wbSvgAbortController = null;
  }

  const backendUp = await probeBackendHealth();
  if (!backendUp) {
    if (state.wb2dPreviewUrl) {
      URL.revokeObjectURL(state.wb2dPreviewUrl);
      state.wb2dPreviewUrl = null;
    }
    imgEl.classList.add('hidden');
    metaEl.textContent = staticSummary;
    metaEl.classList.remove('hidden');
    return;
  }

  const controller = new AbortController();
  wbSvgAbortController = controller;
  const theme = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  try {
    const res = await fetch('./api/molecule/svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
      body: JSON.stringify({ smiles: clean.slice(0, 512), theme }),
      signal: controller.signal
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const svgText = await res.text();
    const nextUrl = URL.createObjectURL(new Blob([svgText], { type: 'image/svg+xml' }));
    if (state.wb2dPreviewUrl) {
      URL.revokeObjectURL(state.wb2dPreviewUrl);
    }
    state.wb2dPreviewUrl = nextUrl;
    imgEl.src = nextUrl;
    imgEl.classList.remove('hidden');
    metaEl.classList.add('hidden');
  } catch (err) {
    if (err && err.name === 'AbortError') return;
    imgEl.classList.add('hidden');
    metaEl.textContent = staticSummary;
    metaEl.classList.remove('hidden');
  } finally {
    if (wbSvgAbortController === controller) {
      wbSvgAbortController = null;
    }
  }
}

export function loadWorkbenchPreset(key) {
  const preset = PRESET_INHIBITORS[key];
  const smiles = typeof preset === 'string' ? preset : preset?.smiles;
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

  state.currentOt2Code = '';
  state.currentOt2Key = '';
  state.latestResistanceData = null;

  if (currentTargetTab === 'presets' && info && (info.pdb || info.pdbId)) {
    const targetPdbId = info.pdbId || info.pdb;
    (async () => {
      const pdbText = (typeof loadPdb === 'function') ? await loadPdb(targetPdbId) : null;
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

function appendSafeLogMarkup(container, rawHtmlOrText) {
  const src = String(rawHtmlOrText ?? '');
  const tagRegex = /<(strong)(?:\s+style="([^"]*)")?>([\s\S]*?)<\/strong>/gi;
  let lastIdx = 0;
  let match;
  while ((match = tagRegex.exec(src)) !== null) {
    if (match.index > lastIdx) {
      container.appendChild(document.createTextNode(src.slice(lastIdx, match.index)));
    }
    const strongEl = document.createElement('strong');
    const styleVal = match[2] || '';
    const colorMatch = styleVal.match(/color:\s*(#[0-9a-fA-F]{3,8}|var\(--[a-zA-Z0-9-]+\))/);
    if (colorMatch) {
      strongEl.style.color = colorMatch[1];
    }
    strongEl.textContent = match[3];
    container.appendChild(strongEl);
    lastIdx = tagRegex.lastIndex;
  }
  if (lastIdx < src.length) {
    container.appendChild(document.createTextNode(src.slice(lastIdx)));
  }
}

export function logEntry(labelTag, agent, role, text, color) {
  const log = document.getElementById('agentLog');
  if (!log) return;
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
  const tsEl = document.getElementById('streamTimestamp');
  if (tsEl) tsEl.textContent = ts;

  const safeColor = /^#[a-fA-F0-9]{3,8}$|^var\(--[a-zA-Z0-9-]+\)$/.test(color || '') ? color : '#76b900';

  const wrapper = document.createElement('div');
  wrapper.className = 'animate-fade-up';

  const card = document.createElement('div');
  card.className = 'flex items-start gap-2.5 p-2.5 rounded-lg';
  card.style.background = 'rgba(22,27,34,0.6)';
  card.style.border = `1px solid ${safeColor.startsWith('#') ? safeColor + '25' : 'rgba(118,185,0,0.2)'}`;

  const dot = document.createElement('span');
  dot.className = 'w-2 h-2 rounded-full mt-1.5 shrink-0';
  dot.style.background = safeColor;

  const contentWrap = document.createElement('div');
  contentWrap.className = 'flex-1 min-w-0';

  const metaRow = document.createElement('div');
  metaRow.className = 'flex items-center gap-2 mb-1';

  const agentSpan = document.createElement('span');
  agentSpan.className = 'font-bold text-[10px] uppercase tracking-wider';
  agentSpan.style.color = safeColor;
  agentSpan.textContent = String(agent || 'Agent');

  const roleSpan = document.createElement('span');
  roleSpan.className = 'text-[9px] text-gray-500 font-mono';
  roleSpan.textContent = String(role || '');

  const timeSpan = document.createElement('span');
  timeSpan.className = 'text-[9px] text-gray-600 ml-auto font-mono';
  timeSpan.textContent = ts;

  metaRow.append(agentSpan, roleSpan, timeSpan);

  const bodyDiv = document.createElement('div');
  bodyDiv.className = 'text-gray-300 leading-relaxed text-[11px] break-words';
  appendSafeLogMarkup(bodyDiv, text);

  contentWrap.append(metaRow, bodyDiv);
  card.append(dot, contentWrap);
  wrapper.appendChild(card);

  log.appendChild(wrapper);
  while (log.children.length > 25) {
    log.removeChild(log.firstChild);
  }
  log.scrollTop = log.scrollHeight;
}

export function updateKpisFromLeads(leads) {
  const list = Array.isArray(leads) ? leads : [];
  if (list.length === 0) return;

  let bestAff = Infinity;
  let bestQed = -Infinity;
  let paretoCount = 0;
  for (const item of list) {
    if (typeof item.affinity === 'number' && item.affinity < bestAff) bestAff = item.affinity;
    if (typeof item.qed === 'number' && item.qed > bestQed) bestQed = item.qed;
    if (item.pareto) paretoCount += 1;
  }

  const kpiAff = document.getElementById('kpiAffinity');
  if (kpiAff && Number.isFinite(bestAff)) kpiAff.textContent = bestAff.toFixed(2);
  const kpiQed = document.getElementById('kpiQed');
  if (kpiQed && Number.isFinite(bestQed)) kpiQed.textContent = bestQed.toFixed(3);
  const kpiSc = document.getElementById('kpiScreened');
  if (kpiSc) kpiSc.textContent = String(state.activeRunResult?.screenedCount || list.length);
  const kpiPar = document.getElementById('kpiPareto');
  if (kpiPar) kpiPar.textContent = String(paretoCount);
}

export function renderRedockDeltaStrip(lead) {
  const affBox = document.getElementById('redockAffinityDisplay');
  if (!affBox || !lead) return;
  const base = state.leadBaselines instanceof Map ? state.leadBaselines.get(lead.id) : null;
  if (!base) {
    affBox.textContent = '';
    return;
  }

  affBox.textContent = '';
  const row = document.createElement('div');
  row.className = 'flex flex-wrap items-center justify-center gap-1.5 text-[10px] font-mono tabular-nums';

  const makeDeltaPill = (label, delta, lowerIsBetter, decimals, unit) => {
    const improved = lowerIsBetter ? delta < -1e-6 : delta > 1e-6;
    const worsened = lowerIsBetter ? delta > 1e-6 : delta < -1e-6;
    const tone = improved
      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
      : worsened
        ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
        : 'bg-slate-800 text-gray-300 border-white/10';
    const sign = delta > 0 ? '+' : '';
    const pill = document.createElement('span');
    pill.className = `px-1.5 py-0.5 rounded border ${tone}`;
    pill.textContent = `${label} ${sign}${delta.toFixed(decimals)}${unit ? ' ' + unit : ''}`;
    return pill;
  };

  if (typeof lead.affinity === 'number' && typeof base.affinity === 'number') {
    row.appendChild(makeDeltaPill('ΔΔG', lead.affinity - base.affinity, true, 2, 'kcal/mol'));
  }
  if (typeof lead.qed === 'number' && typeof base.qed === 'number') {
    row.appendChild(makeDeltaPill('ΔQED', lead.qed - base.qed, false, 3, ''));
  }
  if (typeof lead.sascore === 'number' && typeof base.sascore === 'number') {
    row.appendChild(makeDeltaPill('ΔSA', lead.sascore - base.sascore, true, 2, ''));
  }

  const revertBtn = document.createElement('button');
  revertBtn.type = 'button';
  revertBtn.setAttribute('data-action', 'revert-lead');
  revertBtn.className = 'px-2 py-0.5 rounded border border-cyan-500/40 bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25 font-semibold';
  revertBtn.textContent = 'Revert to Original';
  row.appendChild(revertBtn);

  affBox.appendChild(row);
}

export function revertSelectedLead() {
  const lead = state.currentSelectedLead;
  if (!lead || !(state.leadBaselines instanceof Map) || !state.leadBaselines.has(lead.id)) return;
  const base = state.leadBaselines.get(lead.id);
  Object.assign(lead, structuredClone(base));
  state.leadBaselines.delete(lead.id);
  state.selectedPoseIndex = 0;
  state.activePoseIndex = 0;
  state.leadRevision = (state.leadRevision || 0) + 1;

  updateKpisFromLeads(state.currentLeads);
  renderLeads();
  try {
    renderPareto();
  } catch (_) {}
  showToast(`Reverted ${lead.id} to original baseline.`);
}

export function selectLeadById(leadId) {
  const leads = state.currentLeads || [];
  const idx = leads.findIndex(l => l.id === leadId);
  if (idx >= 0) selectLead(idx);
}

export function renderLeads() {
  const container = document.getElementById('leadsContainer');
  if (!container) return;
  const leads = state.currentLeads || [];
  const countEl = document.getElementById('leadCount');
  if (countEl) countEl.textContent = `${leads.length} candidates`;

  if (leads.length === 0) {
    state.selectedLeadId = null;
    container.innerHTML = `
      <div id="emptyLeadsState" class="flex flex-col items-center justify-center p-8 text-center text-gray-500">
        <svg class="w-7 h-7 mb-2 text-emerald-400/70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 3v6l-4 7a2 2 0 001.7 3h10.6a2 2 0 001.7-3l-4-7V3m-6 0h6"/></svg>
        <div class="text-xs font-semibold text-gray-400">No leads nominated yet</div>
        <div class="text-[10px] text-gray-600 mt-1">Select a target and run autonomous discovery to nominate Pareto-optimal drug candidates.</div>
      </div>
    `;
    const panel = document.getElementById('dossierPanel');
    if (panel) {
      panel.innerHTML = `
        <div class="flex flex-col items-center justify-center h-48 text-center text-gray-600 text-xs">
          <svg class="w-6 h-6 mb-1.5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
          <span>No lead selected</span>
          <span class="text-[10px] text-gray-700 mt-1">Nominated candidates will appear here</span>
        </div>
      `;
    }
    return;
  }

  let selectedIdx = state.selectedLeadId ? leads.findIndex(l => l.id === state.selectedLeadId) : -1;
  if (selectedIdx < 0) {
    selectedIdx = 0;
    state.selectedLeadId = leads[0].id;
  }

  container.innerHTML = leads.map((lead, i) => {
    const isSimulated = Boolean(lead.is_simulated || lead.provenance === 'SIMULATED');
    return `
      <div class="lead-card ${i === selectedIdx ? 'selected' : ''}" data-action="select-lead" data-lead-id="${escapeHtml(lead.id)}" data-lead-index="${i}" role="button" tabindex="0">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="font-mono font-bold text-xs text-white">${escapeHtml(lead.id)}</span>
            ${lead.pareto ? '<span class="badge-green">PARETO</span>' : ''}
            ${isSimulated ? '<span class="badge-simulated px-1.5 py-0.5 text-[9px] rounded font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">SIMULATED</span>' : '<span class="badge-live px-1.5 py-0.5 text-[9px] rounded font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">NIM LIVE</span>'}
          </div>
          <span class="${lead.verdict === 'PASS' ? 'badge-green' : 'badge-yellow'}">${escapeHtml(lead.verdict)}</span>
        </div>
        <div class="grid grid-cols-4 gap-2 text-[10px]">
          <div><div class="text-gray-600">ΔG</div><div class="font-mono font-bold" style="color: var(--nvidia-green);">${escapeHtml(typeof lead.affinity === 'number' ? lead.affinity.toFixed(2) : lead.affinity)}</div></div>
          <div><div class="text-gray-600">QED</div><div class="font-mono font-bold" style="color: var(--cyber-cyan);">${escapeHtml(typeof lead.qed === 'number' ? lead.qed.toFixed(3) : lead.qed)}</div></div>
          <div><div class="text-gray-600">MW</div><div class="font-mono text-gray-300">${escapeHtml(typeof lead.mw === 'number' ? lead.mw.toFixed(1) : lead.mw)}</div></div>
          <div><div class="text-gray-600">SAScore</div><div class="font-mono text-gray-300">${escapeHtml(typeof lead.sascore === 'number' ? lead.sascore.toFixed(2) : lead.sascore)}</div></div>
        </div>
      </div>
    `;
  }).join('');
  selectLead(selectedIdx);
}

export function selectLead(i) {
  document.querySelectorAll('.lead-card').forEach((c, idx) => c.classList.toggle('selected', idx === i));
  const leads = state.currentLeads || [];
  const lead = leads[i];
  if (!lead) return;
  state.currentSelectedLead = lead;
  state.selectedLeadId = lead.id;
  state.activePoseIndex = 0;
  state.selectedPoseIndex = 0;
  state.currentOt2Code = '';
  state.currentOt2Key = '';
  state.latestResistanceData = null;

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
      <div class="rounded-xl overflow-hidden border border-surface-border bg-surface-card relative">
        <div class="p-2 border-b border-surface-border flex items-center justify-between bg-surface-elevated">
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span class="text-[10px] font-bold font-mono text-cyan-300">3D Docked Complex</span>
          </div>
          <div class="flex items-center gap-1">
            <button type="button" data-action="toggle-3d-spin" id="btnSpin" class="px-1.5 py-0.5 text-[9px] rounded bg-surface-card hover:border-cyan-500/50 border border-surface-border text-gray-300 transition-colors">Spin</button>
            <button type="button" data-action="toggle-3d-surface" id="btnSurface" class="px-1.5 py-0.5 text-[9px] rounded bg-surface-card hover:border-cyan-500/50 border border-surface-border text-gray-300 transition-colors">Surface</button>
            <button type="button" data-action="reset-3d-view" aria-label="Recenter 3D view" class="px-1.5 py-0.5 text-[9px] rounded bg-surface-card hover:border-cyan-500/50 border border-surface-border text-gray-300 transition-colors">Reset</button>
            <button type="button" data-action="open-3d-modal" aria-label="Expand 3D viewer" class="px-1.5 py-0.5 text-[9px] rounded bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/25 border border-cyan-500/30 transition-colors font-bold">Expand</button>
          </div>
        </div>
        <div id="molViewer3D" style="width: 100%; height: 210px; position: relative;"></div>
        <div class="p-1.5 bg-surface-elevated border-t border-surface-border flex items-center justify-between text-[9px] text-gray-400">
          <div class="flex items-center gap-2">
            <span><span class="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400"></span> Pocket</span>
            <span><span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Pose</span>
          </div>
          <span id="viewer3dBadge" class="font-mono text-emerald-400 font-bold">DiffDock 3D</span>
        </div>
      </div>

      <!-- Multi-Pose Selector & 3D Contacts & Pose Plausibility -->
      ${Array.isArray(lead.poses) && lead.poses.length > 0 ? `
      <div class="p-2 rounded-xl border border-surface-border bg-black/30 space-y-1.5">
        <div class="text-[10px] font-bold text-gray-300 uppercase tracking-wider flex items-center justify-between">
          <span>Docked Poses (${lead.poses.length})</span>
          <span class="text-[9px] font-mono text-cyan-400">${esc(lead.poses[0]?.provenance || 'SIMULATED')}</span>
        </div>
        <div class="flex flex-wrap gap-1">
          ${lead.poses.map((p, pIdx) => `
            <button type="button" data-action="select-docked-pose" data-arg="${pIdx}" aria-pressed="${pIdx === 0 ? 'true' : 'false'}" class="px-2 py-0.5 text-[10px] font-mono rounded border ${pIdx === 0 ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300' : 'bg-white/5 border-surface-border text-gray-300 hover:border-cyan-500/50'} transition-colors">
              Pose #${Number(p.rank || pIdx + 1)} (${typeof p.predicted_affinity_kcal_mol === 'number' ? p.predicted_affinity_kcal_mol.toFixed(1) : '—'})
            </button>
          `).join('')}
        </div>
      </div>` : ''}

      <!-- MedChem BOILED-Egg & Structural Alerts -->
      <div class="p-2 rounded-xl border border-surface-border bg-black/25 space-y-1 text-[10px]">
        <div class="flex items-center justify-between font-bold text-gray-300 uppercase tracking-wider">
          <span>MedChem Profiling</span>
          ${lead.is_salt_desalted ? '<span class="px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 text-[9px] font-mono">Salt Desalted</span>' : ''}
        </div>
        <div class="flex flex-wrap gap-1">
          <span class="px-1.5 py-0.5 rounded font-mono ${lead.gi_absorption_high ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-gray-400 border border-white/10'}">GI: ${lead.gi_absorption_high ? 'High' : 'Low'}</span>
          <span class="px-1.5 py-0.5 rounded font-mono ${lead.bbb_permeable ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-slate-800 text-gray-400 border border-white/10'}">BBB: ${lead.bbb_permeable ? 'Permeant' : 'Peripheral'}</span>
          <span class="px-1.5 py-0.5 rounded font-mono ${(lead.brenk_alerts || []).length === 0 ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'}">BRENK: ${(lead.brenk_alerts || []).length}</span>
          <span class="px-1.5 py-0.5 rounded font-mono ${(lead.pains_alerts || []).length === 0 ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/40'}">PAINS: ${(lead.pains_alerts || []).length}</span>
        </div>
      </div>

      ${lead.pose_validation && typeof lead.pose_validation === 'object' ? `
      <div id="posePlausibilityContainer" class="p-2 rounded-xl border border-surface-border bg-black/25 space-y-1 text-[10px]">
        <div class="flex items-center justify-between font-bold text-gray-300 uppercase tracking-wider">
          <span>3D Pose Plausibility</span>
          <span class="font-mono text-[9px] ${lead.pose_validation.passes_all ? 'text-emerald-400' : 'text-amber-400'}">${lead.pose_validation.passes_all ? 'PLAUSIBLE' : 'REVIEW'}</span>
        </div>
        <div class="flex flex-wrap gap-1 font-mono text-[9px]">
          <span class="px-1.5 py-0.5 rounded ${lead.pose_validation.bond_geometry_pass ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'}">${lead.pose_validation.bond_geometry_pass ? '✓' : '✗'} Bonds</span>
          <span class="px-1.5 py-0.5 rounded ${lead.pose_validation.receptor_clash_pass ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'}">${lead.pose_validation.receptor_clash_pass ? '✓' : '✗'} Clashes (${Number(lead.pose_validation.receptor_clash_count || 0)})</span>
          <span class="px-1.5 py-0.5 rounded ${lead.pose_validation.planarity_pass ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'}">${lead.pose_validation.planarity_pass ? '✓' : '✗'} Planarity</span>
          <span class="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300">ΔE ${lead.pose_validation.strain_energy_kcal_mol !== null && lead.pose_validation.strain_energy_kcal_mol !== undefined ? Number(lead.pose_validation.strain_energy_kcal_mol).toFixed(1) + ' kcal/mol' : 'N/A'}</span>
          ${lead.pose_validation.covalent_proximity ? '<span class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">Covalent Prox</span>' : ''}
        </div>
      </div>` : ''}

      ${Array.isArray(lead.interaction_contacts) && lead.interaction_contacts.length > 0 ? `
      <div id="contactsContainer" class="p-2 rounded-xl border border-surface-border bg-black/25 space-y-1 text-[10px]">
        <div class="font-bold text-gray-300 uppercase tracking-wider">3D Binding Contacts (Click to Focus)</div>
        <div class="flex flex-wrap gap-1">
          ${lead.interaction_contacts.slice(0, 8).map((c, cIdx) => `
            <button type="button" data-action="focus-contact" data-arg="${cIdx}" data-contact-index="${cIdx}" class="px-1.5 py-0.5 text-[9px] font-mono rounded bg-white/5 hover:bg-cyan-500/15 border border-surface-border text-gray-200 transition-colors">
              ${esc(c.type || 'Contact')}: ${esc(c.residue || '')} (${Number(c.distance_a || 0).toFixed(2)}Å)
            </button>
          `).join('')}
        </div>
      </div>` : ''}

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
          <span>Chemical Workbench</span>
          <div id="workbenchValenceBadge">
            <span class="badge-valence-valid">Valid Chemical Graph</span>
          </div>
        </div>

        <!-- 1-Click Reference Presets -->
        <div class="flex items-center gap-1 mb-2 overflow-x-auto py-0.5">
          <button type="button" data-action="load-wb-preset" data-arg="kras" class="wb-preset-pill">MRTX1133 (KRAS)</button>
          <button type="button" data-action="load-wb-preset" data-arg="egfr" class="wb-preset-pill">Osimertinib (EGFR)</button>
          <button type="button" data-action="load-wb-preset" data-arg="mpro" class="wb-preset-pill">Nirmatrelvir (Mpro)</button>
          <button type="button" data-action="load-wb-preset" data-arg="her2" class="wb-preset-pill">Tucatinib (HER2)</button>
        </div>

        <div id="wb2dPreviewBox" class="mb-1.5 rounded border border-surface-border bg-surface-card p-1.5 flex items-center justify-center min-h-[56px]">
          <img id="wb2dPreviewImg" alt="2D chemical structure preview" class="hidden max-h-[120px] w-auto object-contain"/>
          <span id="wb2dPreviewMeta" class="text-[10px] font-mono text-gray-400 text-center"></span>
        </div>

        <input type="text" id="workbenchSmilesInput" data-input-action="workbench-input" aria-label="Ligand SMILES Structure" value="${safeSmiles}" class="w-full text-[11px] font-mono p-1.5 rounded bg-surface-card border border-surface-border text-gray-200 mb-1.5 focus:outline-none focus:border-cyan-400" />
        
        <!-- Live Biophysical Metric Tile Readout -->
        <div id="workbenchLiveMetrics" class="grid grid-cols-4 gap-1 text-[10px] font-mono text-center p-1.5 rounded bg-surface-card border border-surface-border mb-2">
          <div><span class="text-gray-500 block text-[9px]">ΔG (kcal/mol)</span><span id="wbLiveAffinity" class="text-emerald-400 font-bold">${lead.affinity.toFixed(2)}</span></div>
          <div><span class="text-gray-500 block text-[9px]">QED Score</span><span id="wbLiveQed" class="text-cyan-400 font-bold">${lead.qed.toFixed(3)}</span></div>
          <div><span class="text-gray-500 block text-[9px]">SAScore</span><span id="wbLiveSas" class="text-amber-400 font-bold">${lead.sascore.toFixed(2)}</span></div>
          <div><span class="text-gray-500 block text-[9px]">MW (g/mol)</span><span id="wbLiveMw" class="text-gray-300 font-bold">${(lead.mw || 500).toFixed(0)}</span></div>
        </div>

        <div class="grid grid-cols-3 gap-1 mb-2">
          <button type="button" data-action="tweak-smiles" data-arg="fluorine" class="py-1 text-[10px] bg-surface-card hover:border-cyan-500/50 text-gray-300 rounded border border-surface-border font-mono">+F Fluorine</button>
          <button type="button" data-action="tweak-smiles" data-arg="methyl" class="py-1 text-[10px] bg-surface-card hover:border-cyan-500/50 text-gray-300 rounded border border-surface-border font-mono">+Me Methyl</button>
          <button type="button" data-action="tweak-smiles" data-arg="pyridine" class="py-1 text-[10px] bg-surface-card hover:border-cyan-500/50 text-gray-300 rounded border border-surface-border font-mono">Swap Pyridine</button>
        </div>

        <button type="button" data-action="trigger-redock" class="w-full py-1.5 btn-cta text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1.5">
          <span>Instant Re-Dock Modified Lead</span>
        </button>
        <div id="redockAffinityDisplay" class="mt-1.5 text-center text-xs"></div>
      </div>

      <!-- Dr. Chen's Retrosynthesis Tree & Procedure Card -->
      <div class="p-2.5 rounded-xl border border-amber-500/20 bg-amber-500/5">
        <div class="text-[11px] font-bold text-amber-400 mb-1 flex items-center justify-between">
          <span>Wet-Lab Synthesis Route</span>
          <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-amber-500/20 text-amber-300">${state.activeRunResult?.retrosynthesis?.is_convergent ? 'Convergent BRICS' : 'Linear / Heuristic'}</span>
        </div>
        <div class="text-[10px] text-gray-300 space-y-1 mb-2">
          <div><strong class="text-white">Feasibility:</strong> ${esc(state.activeRunResult?.retrosynthesis?.feasibility || 'Suzuki Coupling + Amide Condensation (Heuristic)')}</div>
        </div>
        ${state.activeRunResult?.retrosynthesis?.route_tree ? renderRetroTreeMarkup(state.activeRunResult.retrosynthesis.route_tree, esc) : ''}
        <div class="pt-2 border-t border-amber-500/20 flex gap-1.5">
          <button type="button" data-action="robot-protocol" class="flex-1 py-1.5 text-[10px] font-bold rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 flex items-center justify-center gap-1 transition-all">
            <span>Opentrons OT-2 Code</span>
          </button>
          <button type="button" data-action="lab-card" class="flex-1 py-1.5 text-[10px] font-bold rounded-lg bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10 flex items-center justify-center gap-1 transition-all">
            <span>Wet-Lab SOP</span>
          </button>
        </div>
      </div>

      <!-- Adaptive Resistance Stress-Test Card -->
      <div class="p-2.5 rounded-xl border border-red-500/25 bg-red-950/20">
        <div class="text-[11px] font-bold text-red-400 mb-1 flex items-center justify-between">
          <span>Adaptive Resistance Stress-Test</span>
          <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-red-500/20 text-red-300 border border-red-500/30">ESM-2 / MolMIM</span>
        </div>
        <p class="text-[10px] text-gray-400 mb-2">Simulate target point mutation clash & auto-evolve escape scaffold via MolMIM latent steering.</p>
        <button type="button" data-action="resistance-test" class="w-full py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-red-600/30 to-purple-600/30 hover:from-red-600/50 hover:to-purple-600/50 text-red-200 border border-red-500/40 flex items-center justify-center gap-1.5 transition-all">
          <span>Run Resistance Stress-Test</span>
        </button>
      </div>

      <!-- Export Buttons -->
      <div class="space-y-1.5 pt-1">
        <button type="button" data-action="generate-ind-pdf" class="w-full py-2.5 text-xs font-bold text-white rounded-lg flex items-center justify-center gap-1.5 transition-all hover:scale-102 glow-green shadow-lg" style="background: linear-gradient(135deg, #1e40af, #2563eb); border: 1px solid rgba(59, 130, 246, 0.6);">
          <span>Download Pre-Clinical Summary (PDF)</span>
          <span class="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/20 text-white font-bold">CMC Template</span>
        </button>
        <button type="button" data-action="download-dossier" class="btn-ghost w-full text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5">
          Export Dossier (.md)
        </button>
        <button type="button" data-action="export-leads-csv" class="btn-ghost w-full text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5">
          Export Leads (.csv)
        </button>
        <button type="button" data-action="download-sdf" class="btn-ghost w-full text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5" style="border-color: rgba(0,241,253,0.3); color: #00f1fd;">
          Export Poses (.sdf)
        </button>
        <button type="button" data-action="export-smiles" class="btn-ghost w-full text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5">
          Export SMILES (.smi)
        </button>
      </div>
    </div>
  `;

  if (state.leadBaselines instanceof Map && state.leadBaselines.has(lead.id)) {
    renderRedockDeltaStrip(lead);
  }
  updateWorkbench2dPreview(lead.smiles || '');
  setTimeout(() => updateLead3DView(lead), 40);
}

export function pushRunHistory(runResult) {
  if (!runResult || !runResult.runId) return;
  const topAff = typeof runResult.topLead?.affinity === 'number'
    ? runResult.topLead.affinity.toFixed(1)
    : '—';
  const snapshot = {
    runId: runResult.runId,
    label: runResult.pdbId || runResult.target || 'RUN',
    pdbId: runResult.pdbId || '',
    topAffinity: topAff,
    runResult: structuredClone(runResult),
    targetPdbText: state.currentTargetPdbText || null,
    provenance: runResult.provenance || 'SIMULATED',
    timestamp: runResult.timestamp || new Date().toISOString()
  };

  state.runHistory = [snapshot, ...(state.runHistory || []).filter(r => r.runId !== snapshot.runId)].slice(0, 3);

  try {
    const lite = state.runHistory.map(r => ({
      runId: r.runId,
      label: r.label,
      pdbId: r.pdbId,
      topAffinity: r.topAffinity,
      provenance: r.provenance,
      timestamp: r.timestamp
    }));
    sessionStorage.setItem('bionemo_run_history_lite', JSON.stringify(lite));
  } catch (_) {}
}

export function renderRunHistoryStrip() {
  const strip = document.getElementById('runHistoryStrip');
  if (!strip) return;
  const list = state.runHistory || [];
  if (list.length === 0) {
    strip.classList.add('hidden');
    strip.textContent = '';
    return;
  }
  strip.classList.remove('hidden');
  strip.textContent = '';
  for (const item of list) {
    const isActive = item.runId === state.runId;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute('data-action', 'restore-run-history');
    btn.setAttribute('data-arg', item.runId);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    btn.className = `px-2 py-0.5 rounded text-[10px] font-mono tabular-nums border transition-colors ${
      isActive
        ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 font-bold'
        : 'bg-white/5 border-surface-border text-gray-300 hover:border-cyan-500/50'
    }`;
    btn.textContent = `${item.label} · ${item.topAffinity}`;
    strip.appendChild(btn);
  }
}

export function restoreRunFromHistory(runId) {
  const entry = (state.runHistory || []).find(r => r.runId === runId);
  if (!entry || !entry.runResult) return;

  state.runId = entry.runId;
  state.activeRunResult = structuredClone(entry.runResult);
  if (typeof window !== 'undefined') window.activeRunResult = state.activeRunResult;
  state.currentLeads = state.activeRunResult.leads || [];
  state.currentTargetPdbText = entry.targetPdbText || state.currentTargetPdbText;
  state.leadBaselines.clear();
  state.selectedLeadId = state.currentLeads[0]?.id || null;
  state.selectedPoseIndex = 0;
  state.leadRevision = 0;

  updateKpisFromLeads(state.currentLeads);
  renderLeads();
  try {
    renderPareto();
  } catch (_) {}
  renderRunHistoryStrip();
  showToast(`Restored run ${entry.label} (${entry.topAffinity} kcal/mol).`);
}

if (typeof window !== 'undefined') {
  window.addEventListener('bionemo:pose-changed', (ev) => {
    const detail = ev?.detail || {};
    const idx = Number(detail.poseIndex || 0);
    const pose = detail.pose || null;
    const lead = state.currentSelectedLead;
    if (!lead || detail.leadId !== lead.id) return;

    document.querySelectorAll('[data-action="select-docked-pose"]').forEach((btn, bIdx) => {
      const active = bIdx === idx;
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      btn.classList.toggle('bg-cyan-500/20', active);
      btn.classList.toggle('border-cyan-400', active);
      btn.classList.toggle('text-cyan-300', active);
    });

    const contactsEl = document.getElementById('contactsContainer');
    const poseContacts = Array.isArray(pose?.interaction_contacts)
      ? pose.interaction_contacts
      : (lead.interaction_contacts || []);
    if (contactsEl && Array.isArray(poseContacts)) {
      const chipWrap = contactsEl.querySelector('.flex.flex-wrap');
      if (chipWrap) {
        chipWrap.textContent = '';
        poseContacts.slice(0, 8).forEach((c, cIdx) => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.setAttribute('data-action', 'focus-contact');
          btn.setAttribute('data-arg', String(cIdx));
          btn.setAttribute('data-contact-index', String(cIdx));
          btn.className = 'px-1.5 py-0.5 text-[9px] font-mono rounded bg-white/5 hover:bg-cyan-500/15 border border-surface-border text-gray-200 transition-colors';
          btn.textContent = `${c.type || 'Contact'}: ${c.residue || ''} (${Number(c.distance_a || 0).toFixed(2)}Å)`;
          chipWrap.appendChild(btn);
        });
      }
    }

    const plausEl = document.getElementById('posePlausibilityContainer');
    const pv = pose?.pose_validation && typeof pose.pose_validation === 'object' ? pose.pose_validation : lead.pose_validation;
    if (plausEl && pv && typeof pv === 'object') {
      const statusSpan = plausEl.querySelector('span.font-mono');
      if (statusSpan) {
        statusSpan.className = `font-mono text-[9px] ${pv.passes_all ? 'text-emerald-400' : 'text-amber-400'}`;
        statusSpan.textContent = pv.passes_all ? 'PLAUSIBLE' : 'REVIEW';
      }
      const pillsWrap = plausEl.querySelector('.flex.flex-wrap');
      if (pillsWrap) {
        pillsWrap.textContent = '';
        const makeBadge = (text, cls) => {
          const s = document.createElement('span');
          s.className = `px-1.5 py-0.5 rounded ${cls}`;
          s.textContent = text;
          return s;
        };
        pillsWrap.appendChild(makeBadge(`${pv.bond_geometry_pass ? '✓' : '✗'} Bonds`, pv.bond_geometry_pass ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'));
        pillsWrap.appendChild(makeBadge(`${pv.receptor_clash_pass ? '✓' : '✗'} Clashes (${Number(pv.receptor_clash_count || 0)})`, pv.receptor_clash_pass ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'));
        pillsWrap.appendChild(makeBadge(`${pv.planarity_pass ? '✓' : '✗'} Planarity`, pv.planarity_pass ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/20 text-red-300'));
        const strainTxt = pv.strain_energy_kcal_mol !== null && pv.strain_energy_kcal_mol !== undefined
          ? `${Number(pv.strain_energy_kcal_mol).toFixed(1)} kcal/mol`
          : 'N/A';
        pillsWrap.appendChild(makeBadge(`ΔE ${strainTxt}`, 'bg-slate-800 text-cyan-300'));
        if (pv.covalent_proximity) {
          pillsWrap.appendChild(makeBadge('Covalent Prox', 'bg-amber-500/20 text-amber-300 border border-amber-500/40'));
        }
      }
    }
  });
}

function renderRetroNodeList(node, esc) {
  if (!node || typeof node !== 'object') return '';
  const smi = esc(String(node.smiles || '').slice(0, 36));
  const rxn = esc(node.reaction_type || 'Step');
  const status = esc(node.status || 'Disconnection Step');
  const isTerminal = !Array.isArray(node.children) || node.children.length === 0;
  const childrenHtml = isTerminal
    ? ''
    : `<ul>${node.children.map(c => renderRetroNodeList(c, esc)).join('')}</ul>`;
  return `
    <li>
      <div class="retro-node ${isTerminal ? 'retro-terminal' : ''}">
        <div class="font-mono text-[9px] text-cyan-300 truncate">${smi || 'Fragment'}</div>
        <div class="text-[9px] font-bold ${isTerminal ? 'text-amber-300' : 'text-emerald-300'}">${rxn}</div>
        <div class="text-[8px] text-gray-400">${status}</div>
      </div>
      ${childrenHtml}
    </li>`;
}

function renderRetroTreeMarkup(tree, esc) {
  if (!tree || typeof tree !== 'object' || !tree.smiles) return '';
  return `<div class="retro-tree-wrap overflow-x-auto pb-2 mb-2"><ul class="retro-tree">${renderRetroNodeList(tree, esc)}</ul></div>`;
}

export function switchTab(tab) {
  ['windows', 'unix', 'docker', 'compare'].forEach(t => {
    const pane = document.getElementById('pane-' + t);
    const tabEl = document.getElementById('tab-' + t);
    if (pane) pane.classList.toggle('hidden', t !== tab);
    if (tabEl) tabEl.classList.toggle('active', t === tab);
  });
}

export async function copyCode(elId, btn) {
  const el = document.getElementById(elId);
  if (!el) return;
  if (await copyToClipboard(el.textContent || '')) {
    if (btn) {
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    }
    showToast('Copied to clipboard.');
  }
}

export function showToast(msg) {
  showPopoverToast(document.getElementById('toast'), msg || 'Copied to clipboard.', 2800);
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
  openModalDialog(modal);
}

export function closeRawReceiptModal() {
  closeModalDialog(document.getElementById('rawReceiptModal'));
}

export async function copyRawReceiptJson() {
  const content = document.getElementById('rawReceiptContent');
  const btnText = document.getElementById('copyReceiptBtnText');
  if (!content) return;
  if (await copyToClipboard(content.textContent || '')) {
    if (btnText) {
      btnText.textContent = 'Copied!';
      setTimeout(() => { btnText.textContent = 'Copy JSON'; }, 2000);
    }
  }
}

export function exportActiveRunJson() {
  const ctx = buildExportContext();
  const payload = {
    schema_version: ctx.schema_version,
    software_version: ctx.software_version,
    exported_at: ctx.exported_at,
    run_id: ctx.run_id,
    target_metadata: ctx.target_metadata,
    provenance: ctx.provenance,
    is_static_demo: ctx.is_static_demo,
    kpis: ctx.kpis,
    selected_lead_id: ctx.selectedLeadId,
    lead_revision: ctx.leadRevision,
    leads: ctx.leads,
    retrosynthesis: ctx.retrosynthesis,
    baseline_diffs: ctx.baseline_diffs,
    legal_notice: ctx.legal_notice
  };

  const jsonStr = JSON.stringify(
    payload,
    (_k, v) => (typeof v === 'number' && !Number.isFinite(v) ? null : v),
    2
  );
  const filename = buildExportFilename(ctx, 'run', 'json');
  downloadBlob(jsonStr, filename, 'application/json');
  showToast('Exported v2.3.0 discovery run JSON.');
}
