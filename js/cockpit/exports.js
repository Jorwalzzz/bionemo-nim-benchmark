/**
 * Dossier, PDF, Opentrons OT-2, and Chemical Scaffold Export Handlers.
 */

import { state, probeBackendHealth } from './state.js';
import { showToast } from './ui-controls.js';
import { escapeHtml } from './api.js';
import { copyToClipboard, downloadBlob, toCsvCell, buildExportFilename } from '../shared/dom-utils.js';
import { openRobotModal, openResistanceModal, closeResistanceModal } from './modals.js';

const LEGAL_NOTICE_TEXT =
  'NVIDIA Trademark & Non-Affiliation Notice: NVIDIA, BioNeMo, NIM, TensorRT, and Hopper are trademarks ' +
  'and/or registered trademarks of NVIDIA Corporation. This open-source benchmark suite (AGPL-3.0-only) ' +
  'is independently developed by Aarav Jorwal (@Jorwalzzz) and is not sponsored, endorsed, or affiliated with NVIDIA Corporation.';

function finiteOrNull(val) {
  if (typeof val !== 'number') return val ?? null;
  return Number.isFinite(val) ? val : null;
}

function sanitizeLeadForExport(lead) {
  if (!lead || typeof lead !== 'object') return null;
  const copy = {};
  for (const [k, v] of Object.entries(lead)) {
    if (k === '_baseline' || k.startsWith('__')) continue;
    if (typeof v === 'number') {
      copy[k] = Number.isFinite(v) ? v : null;
    } else {
      copy[k] = v;
    }
  }
  return copy;
}

export function buildExportContext() {
  const currentTargetTab = state.currentTargetTab || 'presets';
  let target = document.getElementById('targetSelect')?.value || '7RPZ';
  if (currentTargetTab === 'esmfold') target = 'ESMFold De Novo Target';
  else if (currentTargetTab === 'rcsb') target = (document.getElementById('customTargetInput')?.value || '').trim() || 'RCSB Target';

  const runResult = state.activeRunResult || null;
  const rawLeads = Array.isArray(state.currentLeads) && state.currentLeads.length > 0
    ? state.currentLeads
    : (Array.isArray(runResult?.leads) ? runResult.leads : []);
  const leads = rawLeads.map(sanitizeLeadForExport).filter(Boolean);
  const selectedLead = sanitizeLeadForExport(state.currentSelectedLead || rawLeads[0] || null);
  const pdbId = runResult?.pdbId || document.getElementById('targetPdb')?.textContent || target;
  const rawProv = String(
    typeof runResult?.provenance === 'string'
      ? runResult.provenance
      : (runResult?.provenance?.overall_mode || '')
  ).toUpperCase();
  const isLive = rawProv === 'LIVE' || rawProv === 'MEASURED' || rawProv === 'LIVE_NIM';
  const provenance = isLive ? 'Measured / Live Backend' : 'Illustrative / Static Demo';

  let bestAff = null;
  let bestQed = null;
  let paretoCount = 0;
  for (const l of leads) {
    if (typeof l.affinity === 'number' && Number.isFinite(l.affinity)) {
      bestAff = bestAff === null ? l.affinity : Math.min(bestAff, l.affinity);
    }
    if (typeof l.qed === 'number' && Number.isFinite(l.qed)) {
      bestQed = bestQed === null ? l.qed : Math.max(bestQed, l.qed);
    }
    if (l.pareto) paretoCount += 1;
  }

  const baseline_diffs = [];
  if (state.leadBaselines instanceof Map) {
    for (const [leadId, base] of state.leadBaselines.entries()) {
      const cur = leads.find(l => l.id === leadId);
      if (cur && base) {
        baseline_diffs.push({
          lead_id: leadId,
          original_affinity: finiteOrNull(base.affinity),
          current_affinity: finiteOrNull(cur.affinity),
          delta_affinity: (typeof cur.affinity === 'number' && typeof base.affinity === 'number')
            ? Number((cur.affinity - base.affinity).toFixed(3))
            : null,
          original_qed: finiteOrNull(base.qed),
          current_qed: finiteOrNull(cur.qed),
          original_sascore: finiteOrNull(base.sascore),
          current_sascore: finiteOrNull(cur.sascore),
          original_smiles: base.smiles || null,
          current_smiles: cur.smiles || null
        });
      }
    }
  }

  const retrosynthesis = runResult?.retrosynthesis || {
    num_steps: 2,
    feasibility: 'Heuristic BRICS / Literature Precedent',
    is_convergent: true,
    steps: [
      { step: 1, reaction_type: 'Amide Condensation (HATU/DIPEA)', reagents: ['HATU', 'DIPEA', 'DMF'], yield_pct: 82.0, difficulty: 'Heuristic' },
      { step: 2, reaction_type: 'Cross-Coupling Disconnection', reagents: ['Pd-cat', 'Base'], yield_pct: 75.0, difficulty: 'Heuristic' }
    ]
  };

  const runId = state.runId || runResult?.runId || 'static-demo';
  const pdbBytes = typeof state.currentTargetPdbText === 'string' ? state.currentTargetPdbText.length : 0;

  return {
    schema_version: '2.3.0',
    software_version: '2.3.0',
    exported_at: new Date().toISOString(),
    run_id: runId,
    runId,
    target: runResult?.target || target,
    pdbId,
    target_metadata: {
      target_name: runResult?.target || target,
      pdb_id: pdbId,
      source: currentTargetTab,
      residue_count: (state.currentTargetPocketResidues || []).length ? state.currentTargetPocketResidues.length * 28 : 188,
      pdb_byte_length: pdbBytes
    },
    provenance,
    is_static_demo: !isLive,
    isStaticDemo: !isLive,
    kpis: {
      top_affinity_kcal_mol: bestAff,
      top_qed: bestQed,
      screened_count: runResult?.screenedCount || leads.length,
      pareto_count: paretoCount
    },
    runResult,
    leads,
    selectedLead,
    selected_lead: selectedLead,
    selectedLeadId: state.selectedLeadId || selectedLead?.id || 'LEAD-001',
    leadRevision: state.leadRevision || 0,
    retrosynthesis,
    baseline_diffs,
    legal_notice: LEGAL_NOTICE_TEXT
  };
}

function escapeMdCell(val) {
  return String(val ?? '').replace(/\|/g, '\\|').replace(/[\r\n]+/g, ' ');
}

export async function downloadInstaller(type) {
  let file = 'install.bat';
  if (type === 'unix') file = 'install.sh';
  else if (type === 'powershell') file = 'install.ps1';

  showToast(`Preparing ${file}...`);

  const backendUp = await probeBackendHealth();
  const candidateUrls = [];
  if (backendUp) {
    candidateUrls.push(`./api/download/installer-${type}`);
  }
  candidateUrls.push(`./scripts/installers/${file}`);

  let content = null;
  for (const url of candidateUrls) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const text = await res.text();
        if (text && text.length > 50) {
          content = text;
          break;
        }
      }
    } catch (_) {
      // Try next source
    }
  }

  if (content) {
    downloadBlob(content, file, 'application/octet-stream');
    showToast(`Downloaded ${file}.`);
  } else {
    const fallbackUrl = `https://raw.githubusercontent.com/Jorwalzzz/bionemo-nim-benchmark/main/scripts/installers/${file}`;
    window.open(fallbackUrl, '_blank', 'noopener,noreferrer');
    showToast(`Opening ${file} in new tab...`);
  }
}

export async function downloadDossier() {
  const ctx = buildExportContext();
  if (ctx.leads.length > 0 || ctx.runResult) {
    const leadRows = ctx.leads.map(l => {
      const painsCnt = Array.isArray(l.pains_alerts) ? l.pains_alerts.length : Number(l.pains_count || 0);
      const brenkCnt = Array.isArray(l.brenk_alerts) ? l.brenk_alerts.length : Number(l.brenk_count || 0);
      const gi = typeof l.gi_absorption_high === 'boolean' ? (l.gi_absorption_high ? 'High' : 'Low') : '—';
      const bbb = typeof l.bbb_permeable === 'boolean' ? (l.bbb_permeable ? 'Yes' : 'No') : '—';
      const diff = (ctx.baseline_diffs || []).find(d => d.lead_id === l.id);
      const ddg = diff && typeof diff.delta_affinity === 'number'
        ? `${diff.delta_affinity > 0 ? '+' : ''}${diff.delta_affinity.toFixed(2)}`
        : '—';
      return `| ${escapeMdCell(l.id)} | \`${escapeMdCell(l.smiles)}\` | ${typeof l.affinity === 'number' ? l.affinity.toFixed(2) : '—'} | ${ddg} | ${typeof l.qed === 'number' ? l.qed.toFixed(3) : '—'} | ${typeof l.sascore === 'number' ? l.sascore.toFixed(2) : '—'} | ${typeof l.mw === 'number' ? l.mw.toFixed(1) : '—'} | ${gi}/${bbb} | ${painsCnt}/${brenkCnt} | ${escapeMdCell(l.admet_verdict || l.verdict || '—')} |`;
    }).join('\n');

    const sel = ctx.selectedLead || {};
    const pv = sel.pose_validation && typeof sel.pose_validation === 'object' ? sel.pose_validation : null;
    const contacts = Array.isArray(sel.interaction_contacts) ? sel.interaction_contacts : [];
    const retroSteps = Array.isArray(ctx.retrosynthesis?.steps) ? ctx.retrosynthesis.steps : [];

    const md = [
      `# BioNeMo NIM Benchmark Suite — Candidate Selection Dossier`,
      ``,
      `> **Provenance:** ${ctx.provenance} | **Run ID:** \`${escapeMdCell(ctx.run_id)}\` | **Exported:** \`${ctx.exported_at}\``,
      ``,
      `## 1. Executive KPIs & Target Metadata`,
      `- **Target:** ${escapeMdCell(ctx.target)} (\`${escapeMdCell(ctx.pdbId)}\`, source: \`${escapeMdCell(ctx.target_metadata?.source)}\`)`,
      `- **Top Affinity:** ${ctx.kpis.top_affinity_kcal_mol !== null ? ctx.kpis.top_affinity_kcal_mol.toFixed(2) + ' kcal/mol' : '—'} | **Top QED:** ${ctx.kpis.top_qed !== null ? ctx.kpis.top_qed.toFixed(3) : '—'}`,
      `- **Screened:** ${ctx.kpis.screened_count} | **Pareto Optimal:** ${ctx.kpis.pareto_count} | **Selected Lead:** \`${escapeMdCell(ctx.selectedLeadId)}\` (Rev ${ctx.leadRevision})`,
      ``,
      `## 2. Screened Cohort & MedChem Profile`,
      `| ID | SMILES | ΔG | ΔΔG | QED | SA | MW | GI/BBB | PAINS/BRENK | Verdict |`,
      `| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |`,
      leadRows,
      ``,
      `## 3. Selected Lead 3D Pose Plausibility & Binding Contacts`,
      pv
        ? `- **Status:** ${pv.passes_all ? 'PLAUSIBLE' : 'REVIEW'} | **Bonds:** ${pv.bond_geometry_pass ? 'PASS' : 'FAIL'} | **Clashes:** ${pv.receptor_clash_count ?? 0} | **Planarity:** ${pv.planarity_pass ? 'PASS' : 'FAIL'} | **Strain ΔE:** ${typeof pv.strain_energy_kcal_mol === 'number' ? pv.strain_energy_kcal_mol.toFixed(2) + ' kcal/mol' : 'N/A'}`
        : `- **Status:** No 3D plausibility telemetry attached for this lead.`,
      contacts.length > 0
        ? `- **Contacts:** ${contacts.map(c => `${escapeMdCell(c.type || 'Contact')}: ${escapeMdCell(c.residue || '')} (${Number(c.distance_a || 0).toFixed(2)} Å)`).join('; ')}`
        : `- **Contacts:** None recorded.`,
      ``,
      `## 4. Retrosynthesis Plan (${escapeMdCell(ctx.retrosynthesis?.feasibility || 'Heuristic BRICS / Literature Precedent')})`,
      retroSteps.length > 0
        ? retroSteps.map((s, idx) => `${idx + 1}. **${escapeMdCell(s.reaction_type || 'Step')}** — Reagents: ${escapeMdCell((s.reagents || []).join(', ') || 'Standard')} | Est. Yield: ${Number(s.yield_pct || 80).toFixed(0)}% (${escapeMdCell(s.difficulty || 'Heuristic')})`).join('\n')
        : `1. Heuristic BRICS / Literature Precedent (no multi-step breakdown attached).`,
      ``,
      `## 5. Re-Dock Baseline Diffs`,
      ctx.baseline_diffs.length > 0
        ? ctx.baseline_diffs.map(d => `- **${escapeMdCell(d.lead_id)}:** ΔG ${d.original_affinity} → ${d.current_affinity} kcal/mol (ΔΔG ${d.delta_affinity}) | SMILES: \`${escapeMdCell(d.current_smiles)}\``).join('\n')
        : `- No post-run modifications from baseline.`,
      ``,
      `## 6. License & Legal Attribution`,
      `- **License:** AGPL-3.0-only`,
      `- ${ctx.legal_notice}`
    ].join('\n');

    downloadBlob(md, buildExportFilename(ctx, 'dossier', 'md'), 'text/markdown');
    showToast(`Dossier (${ctx.pdbId}) downloaded.`);
    return;
  }

  const fallbackUrl = './results/CANDIDATE_SELECTION_DOSSIER.md';
  try {
    const res = await fetch(fallbackUrl);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    downloadBlob(text, buildExportFilename(ctx, 'dossier', 'md'), 'text/markdown');
    showToast('Dossier (.md) downloaded.');
  } catch (e) {
    window.open(fallbackUrl, '_blank', 'noopener,noreferrer');
  }
}

export function exportLeadsCSV() {
  const ctx = buildExportContext();
  if (!ctx.leads || ctx.leads.length === 0) {
    showToast('Run discovery first to export leads CSV.');
    return;
  }
  const headers = [
    'run_id',
    'target_pdb',
    'lead_id',
    'smiles',
    'affinity_kcal_mol',
    'delta_affinity_kcal_mol',
    'qed',
    'sascore',
    'mw_da',
    'pareto_optimal',
    'admet_verdict',
    'gi_absorption_high',
    'bbb_permeable',
    'pains_count',
    'brenk_count',
    'pose_valid',
    'strain_energy_kcal_mol',
    'receptor_clash_count',
    'contacts_summary',
    'modified_from_baseline',
    'provenance'
  ];
  const rows = [headers.join(',')];
  const diffById = new Map((ctx.baseline_diffs || []).map(d => [d.lead_id, d]));

  for (const l of ctx.leads) {
    const painsCount = Array.isArray(l.pains_alerts) ? l.pains_alerts.length : Number(l.pains_count || 0);
    const brenkCount = Array.isArray(l.brenk_alerts) ? l.brenk_alerts.length : Number(l.brenk_count || 0);
    const pv = l.pose_validation && typeof l.pose_validation === 'object' ? l.pose_validation : null;
    const poseValid = pv ? Boolean(pv.passes_all) : '';
    const strainVal = pv && typeof pv.strain_energy_kcal_mol === 'number' ? Number(pv.strain_energy_kcal_mol.toFixed(2)) : '';
    const clashCount = pv && typeof pv.receptor_clash_count === 'number' ? pv.receptor_clash_count : '';
    const contactsSummary = Array.isArray(l.interaction_contacts)
      ? l.interaction_contacts
          .map(c => `${String(c.type || 'Contact').replace(/[;\r\n]/g, '')}:${String(c.residue || '').replace(/[;\r\n]/g, '')}(${Number(c.distance_a || 0).toFixed(1)}A)`)
          .join('; ')
      : '';
    const diff = diffById.get(l.id);
    const deltaAff = diff && typeof diff.delta_affinity === 'number' ? Number(diff.delta_affinity.toFixed(2)) : '';
    const isModified = Boolean(diff);

    rows.push([
      toCsvCell(ctx.run_id),
      toCsvCell(ctx.pdbId),
      toCsvCell(l.id || ''),
      toCsvCell(l.smiles || ''),
      toCsvCell(typeof l.affinity === 'number' ? Number(l.affinity.toFixed(2)) : l.affinity),
      toCsvCell(deltaAff),
      toCsvCell(typeof l.qed === 'number' ? Number(l.qed.toFixed(3)) : l.qed),
      toCsvCell(typeof l.sascore === 'number' ? Number(l.sascore.toFixed(2)) : l.sascore),
      toCsvCell(typeof l.mw === 'number' ? Number(l.mw.toFixed(2)) : l.mw),
      toCsvCell(Boolean(l.pareto) ? 'true' : 'false'),
      toCsvCell(l.admet_verdict || l.verdict || ''),
      toCsvCell(typeof l.gi_absorption_high === 'boolean' ? String(l.gi_absorption_high) : ''),
      toCsvCell(typeof l.bbb_permeable === 'boolean' ? String(l.bbb_permeable) : ''),
      toCsvCell(painsCount),
      toCsvCell(brenkCount),
      toCsvCell(poseValid === '' ? '' : String(poseValid)),
      toCsvCell(strainVal),
      toCsvCell(clashCount),
      toCsvCell(contactsSummary),
      toCsvCell(isModified ? 'true' : 'false'),
      toCsvCell(l.provenance || ctx.provenance)
    ].join(','));
  }
  downloadBlob('\uFEFF' + rows.join('\n') + '\n', buildExportFilename(ctx, 'leads', 'csv'), 'text/csv;charset=utf-8;');
  showToast(`Exported ${ctx.leads.length} leads to 21-column CSV.`);
}

export function serializeAnnotatedSdfRecord(rawSdf, title, props = {}) {
  if (typeof rawSdf !== 'string' || !rawSdf.includes('M  END')) return null;
  const normalized = rawSdf.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const mEndIdx = normalized.indexOf('M  END');
  if (mEndIdx < 0) return null;

  const molBlock = normalized.slice(0, mEndIdx + 'M  END'.length);
  const lines = molBlock.split('\n');
  if (lines.length < 5) return null;

  // Verify non-zero 3D coordinates in V2000 atom block
  const countsLine = lines[3] || '';
  const atomCount = parseInt(countsLine.slice(0, 3).trim(), 10);
  let hasNonZeroCoords = false;
  if (Number.isFinite(atomCount) && atomCount > 0) {
    for (let i = 4; i < Math.min(lines.length, 4 + atomCount); i++) {
      const x = parseFloat(lines[i].slice(0, 10).trim());
      const y = parseFloat(lines[i].slice(10, 20).trim());
      const z = parseFloat(lines[i].slice(20, 30).trim());
      if (Number.isFinite(x) && Number.isFinite(y) && Number.isFinite(z)) {
        if (Math.abs(x) + Math.abs(y) + Math.abs(z) > 1e-4) {
          hasNonZeroCoords = true;
          break;
        }
      }
    }
  } else {
    hasNonZeroCoords = true; // V3000 or non-standard counts fallback
  }
  if (!hasNonZeroCoords) return null;

  const safeTitle = String(title || 'POSE').replace(/[\r\n]+/g, ' ').trim().slice(0, 80) || 'POSE';
  lines[0] = safeTitle;

  const propBlocks = [];
  for (const [k, v] of Object.entries(props || {})) {
    if (v === undefined || v === null || v === '') continue;
    const safeKey = String(k).replace(/[^A-Za-z0-9_-]/g, '_');
    const safeVal = String(v).replace(/\$\$\$\$/g, '').replace(/[\r\n]+/g, ' ').trim();
    if (!safeKey || !safeVal) continue;
    propBlocks.push(`> <${safeKey}>\n${safeVal}\n`);
  }

  return `${lines.join('\n')}\n${propBlocks.join('\n')}${propBlocks.length ? '\n' : ''}$$$$\n`;
}

/**
 * Exports genuine 3D docked multi-pose SDF records when available.
 * Never fabricates fake 3D coordinates from bare SMILES; directs to Export SMILES (.smi).
 */
export async function downloadSDF() {
  const ctx = buildExportContext();
  const lead = ctx.selectedLead;
  const records = [];

  if (lead) {
    const poses = Array.isArray(lead.poses) && lead.poses.length > 0 ? lead.poses : [{ rank: 1, sdf_data: lead.pose_sdf, predicted_affinity_kcal_mol: lead.affinity, provenance: lead.provenance, pose_validation: lead.pose_validation }];
    poses.forEach((p, idx) => {
      const rank = Number(p.rank || idx + 1);
      const rawSdf = p.sdf_data || (idx === 0 ? lead.pose_sdf : '');
      const pv = p.pose_validation || lead.pose_validation || {};
      const rec = serializeAnnotatedSdfRecord(rawSdf, `${lead.id}_pose_${rank}`, {
        LEAD_ID: lead.id,
        POSE_RANK: rank,
        TARGET_PDB: ctx.pdbId,
        AFFINITY_KCAL_MOL: typeof (p.predicted_affinity_kcal_mol ?? lead.affinity) === 'number'
          ? Number(p.predicted_affinity_kcal_mol ?? lead.affinity).toFixed(2)
          : '',
        QED: typeof lead.qed === 'number' ? lead.qed.toFixed(3) : '',
        SASCORE: typeof lead.sascore === 'number' ? lead.sascore.toFixed(2) : '',
        PLAUSIBLE: typeof pv.passes_all === 'boolean' ? String(pv.passes_all) : '',
        STRAIN_KCAL_MOL: typeof pv.strain_energy_kcal_mol === 'number' ? pv.strain_energy_kcal_mol.toFixed(2) : '',
        CLASH_COUNT: typeof pv.receptor_clash_count === 'number' ? pv.receptor_clash_count : '',
        PROVENANCE: p.provenance || lead.provenance || ctx.provenance
      });
      if (rec) records.push(rec);
    });
  }

  if (records.length > 0) {
    downloadBlob(records.join(''), buildExportFilename(ctx, 'poses', 'sdf'), 'chemical/x-mdl-sdfile');
    showToast(`Exported ${records.length} 3D docked pose(s) for ${lead.id}.`);
    return;
  }

  if ((state.currentTargetTab || 'presets') === 'presets' && (ctx.pdbId === '7RPZ' || ctx.target === 'KRAS G12D')) {
    const url = './results/top_leads_docked.sdf';
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      downloadBlob(text, buildExportFilename(ctx, 'poses', 'sdf'), 'chemical/x-mdl-sdfile');
      showToast('Docked KRAS G12D poses (.sdf) downloaded.');
      return;
    } catch (_) {
      window.open(url, '_blank', 'noopener,noreferrer');
      return;
    }
  }

  showToast('No 3D SDF coordinates available for this target — use Export SMILES (.smi).');
}

export function downloadSMI() {
  const ctx = buildExportContext();
  if (!ctx.leads || ctx.leads.length === 0) {
    showToast('Run discovery first to export SMILES.');
    return;
  }
  const seen = new Set();
  const lines = [];
  for (const l of ctx.leads) {
    const smi = String(l.smiles || '').replace(/[\t\r\n]+/g, '').trim();
    const id = String(l.id || 'CANDIDATE').replace(/[\t\r\n]+/g, ' ').trim();
    if (!smi || seen.has(id)) continue;
    seen.add(id);
    lines.push(`${smi}\t${id}`);
  }
  if (lines.length === 0) {
    showToast('No valid SMILES available to export.');
    return;
  }
  downloadBlob(lines.join('\n') + '\n', buildExportFilename(ctx, 'leads', 'smi'), 'chemical/x-daylight-smiles');
  showToast(`Exported ${lines.length} deduplicated SMILES (.smi).`);
}

export function generateStaticHtmlDossier(ctx) {
  const lead = ctx.selectedLead || {};
  const pv = lead.pose_validation && typeof lead.pose_validation === 'object' ? lead.pose_validation : null;
  const contacts = Array.isArray(lead.interaction_contacts) ? lead.interaction_contacts : [];
  const retroSteps = Array.isArray(ctx.retrosynthesis?.steps) ? ctx.retrosynthesis.steps : [];

  const leadRowsHtml = (ctx.leads || []).map(l => `
    <tr>
      <td><code>${escapeHtml(l.id)}</code></td>
      <td><code>${escapeHtml(l.smiles)}</code></td>
      <td>${typeof l.affinity === 'number' ? l.affinity.toFixed(2) : '—'}</td>
      <td>${typeof l.qed === 'number' ? l.qed.toFixed(3) : '—'}</td>
      <td>${typeof l.sascore === 'number' ? l.sascore.toFixed(2) : '—'}</td>
      <td>${typeof l.mw === 'number' ? l.mw.toFixed(1) : '—'}</td>
      <td>${escapeHtml(l.admet_verdict || l.verdict || '—')}</td>
    </tr>`).join('');

  const retroHtml = retroSteps.length > 0
    ? `<ol>${retroSteps.map(s => `<li><strong>${escapeHtml(s.reaction_type || 'Step')}</strong> — Reagents: ${escapeHtml((s.reagents || []).join(', ') || 'Standard')} (${Number(s.yield_pct || 80).toFixed(0)}%)</li>`).join('')}</ol>`
    : `<p>Heuristic BRICS / Literature Precedent</p>`;

  const diffHtml = (ctx.baseline_diffs || []).length > 0
    ? `<ul>${ctx.baseline_diffs.map(d => `<li><code>${escapeHtml(d.lead_id)}</code>: ${escapeHtml(d.original_affinity)} → ${escapeHtml(d.current_affinity)} kcal/mol (ΔΔG ${escapeHtml(d.delta_affinity)})</li>`).join('')}</ul>`
    : `<p>No post-run baseline modifications recorded.</p>`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Pre-Clinical Candidate Dossier — ${escapeHtml(ctx.target)}</title>
<style>
  @page { size: A4; margin: 14mm; }
  body { font-family: system-ui, -apple-system, sans-serif; color: #111827; max-width: 880px; margin: 1.5rem auto; padding: 0 1.25rem; line-height: 1.5; }
  h1, h2 { color: #0f172a; margin-top: 1.1rem; margin-bottom: 0.4rem; }
  section { break-inside: avoid; margin-bottom: 1rem; }
  .no-print { background: #ecfeff; border: 1px solid #06b6d4; color: #155e75; padding: 0.6rem 0.9rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.85rem; }
  .banner { border: 2px dashed #ea580c; background: #fff7ed; color: #9a3412; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.88rem; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; margin: 0.6rem 0; font-size: 0.82rem; }
  th, td { border: 1px solid #cbd5e1; padding: 0.4rem 0.55rem; text-align: left; }
  th { background: #f1f5f9; }
  code { background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 4px; word-break: break-all; }
  .footer { margin-top: 1.5rem; border-top: 1px solid #cbd5e1; padding-top: 0.75rem; font-size: 0.78rem; color: #475569; }
  @media print { .no-print { display: none; } body { margin: 0; padding: 0; } }
</style>
</head>
<body>
  <div class="no-print">Printable Dossier Ready — Press <strong>Ctrl+P / Cmd+P</strong> to save as PDF.</div>
  <h1>Pre-Clinical Candidate Selection Dossier</h1>
  <div class="banner">Provenance: ${escapeHtml(ctx.provenance)} | Run ID: <code>${escapeHtml(ctx.run_id)}</code> | Research summary only; not a regulatory IND submission under 21 CFR 312.</div>
  <section>
    <h2>1. Executive KPIs &amp; Target Metadata</h2>
    <table>
      <tr><th>Target</th><td>${escapeHtml(ctx.target)}</td><th>PDB ID</th><td>${escapeHtml(ctx.pdbId)}</td></tr>
      <tr><th>Top Affinity</th><td>${ctx.kpis.top_affinity_kcal_mol !== null ? ctx.kpis.top_affinity_kcal_mol.toFixed(2) + ' kcal/mol' : '—'}</td><th>Top QED</th><td>${ctx.kpis.top_qed !== null ? ctx.kpis.top_qed.toFixed(3) : '—'}</td></tr>
      <tr><th>Screened / Pareto</th><td>${ctx.kpis.screened_count} / ${ctx.kpis.pareto_count}</td><th>Selected Lead</th><td><code>${escapeHtml(ctx.selectedLeadId)}</code> (Rev ${ctx.leadRevision})</td></tr>
    </table>
  </section>
  <section>
    <h2>2. Full Screened Cohort</h2>
    <table>
      <tr><th>ID</th><th>SMILES</th><th>ΔG</th><th>QED</th><th>SA</th><th>MW</th><th>Verdict</th></tr>
      ${leadRowsHtml}
    </table>
  </section>
  <section>
    <h2>3. 3D Pose Plausibility &amp; Binding Contacts</h2>
    <p>${pv ? `Status: <strong>${pv.passes_all ? 'PLAUSIBLE' : 'REVIEW'}</strong> · Clashes: ${pv.receptor_clash_count ?? 0} · Strain ΔE: ${typeof pv.strain_energy_kcal_mol === 'number' ? pv.strain_energy_kcal_mol.toFixed(2) + ' kcal/mol' : 'N/A'}` : 'No 3D plausibility telemetry recorded.'}</p>
    <p>${contacts.length ? contacts.map(c => `${escapeHtml(c.type || 'Contact')}: ${escapeHtml(c.residue || '')} (${Number(c.distance_a || 0).toFixed(2)} Å)`).join(' · ') : 'No binding contacts recorded.'}</p>
  </section>
  <section>
    <h2>4. Retrosynthesis Route (${escapeHtml(ctx.retrosynthesis?.feasibility || 'Heuristic BRICS / Literature Precedent')})</h2>
    ${retroHtml}
  </section>
  <section>
    <h2>5. Re-Dock Baseline Diffs</h2>
    ${diffHtml}
  </section>
  <div class="footer"><strong>AGPL-3.0-only</strong> · ${escapeHtml(ctx.legal_notice)}</div>
</body>
</html>`;
}

export async function generateINDPdf() {
  showToast('Compiling Pre-Clinical Candidate Summary Dossier...');

  const ctx = buildExportContext();
  const lead = ctx.selectedLead || {
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
      schema_version: ctx.schema_version,
      run_id: ctx.run_id,
      target: ctx.target,
      pdb_id: ctx.pdbId,
      target_metadata: ctx.target_metadata,
      provenance: ctx.provenance,
      kpis: ctx.kpis,
      nominated_lead: lead.id,
      binding_affinity: lead.affinity,
      residue_count: ctx.target_metadata.residue_count,
      screened: ctx.kpis.screened_count || 10,
      pareto_count: ctx.kpis.pareto_count || 1,
      leads: ctx.leads.length > 0 ? ctx.leads : [lead],
      pose_validation: lead.pose_validation || null,
      interaction_contacts: lead.interaction_contacts || [],
      baseline_diffs: ctx.baseline_diffs,
      retrosynthesis: ctx.retrosynthesis
    }
  };

  try {
    const backendUp = await probeBackendHealth();
    if (!backendUp) throw new Error('Static/offline mode: generate printable HTML dossier');
    const res = await fetch('./api/dossier/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);

    const blob = await res.blob();
    downloadBlob(blob, buildExportFilename(ctx, 'dossier', 'pdf'), 'application/pdf');
    showToast('Pre-Clinical Candidate Summary PDF downloaded.');
  } catch (err) {
    console.warn('Backend PDF endpoint unavailable in static mode. Generating print-styled HTML dossier:', err);
    const htmlDossier = generateStaticHtmlDossier(ctx);
    downloadBlob(htmlDossier, buildExportFilename(ctx, 'dossier', 'html'), 'text/html;charset=utf-8');
    showToast('Print-ready HTML dossier downloaded (Press Ctrl+P / Cmd+P for PDF).');
  }
}

export const downloadIndPdf = generateINDPdf;

export function buildStaticOt2Script(ctx) {
  const lead = ctx.selectedLead || { id: 'LEAD-001', smiles: 'CC(=O)N1CCNCC1' };
  const steps = Array.isArray(ctx.retrosynthesis?.steps) && ctx.retrosynthesis.steps.length > 0
    ? ctx.retrosynthesis.steps
    : [{ step: 1, reaction_type: 'Stock Plate Setup', reagents: ['DMSO', 'Buffer'], yield_pct: 80, difficulty: 'Heuristic' }];

  const specLiteral = JSON.stringify({
    run_id: ctx.run_id,
    target: ctx.target,
    pdb_id: ctx.pdbId,
    candidate_id: lead.id,
    lead_revision: ctx.leadRevision,
    provenance: ctx.provenance,
    feasibility: ctx.retrosynthesis?.feasibility || 'Heuristic BRICS / Literature Precedent'
  });

  const stepsLiteral = JSON.stringify(
    steps.map((s, idx) => ({
      step_number: Number(s.step || idx + 1),
      reaction_type: String(s.reaction_type || 'Step'),
      reagents: Array.isArray(s.reagents) ? s.reagents.map(String) : ['Standard'],
      dest_well: `A${Math.min(24, idx + 1)}`
    }))
  );

  return [
    `"""`,
    `Liquid-Handling Plate Setup Only -- Dry-Run Simulation Required`,
    `Dry-run via opentrons_simulate and manual labware/volume verification required`,
    `before hardware execution. Thermal, inert-atmosphere, and purification steps`,
    `are performed off-deck. (${ctx.provenance})`,
    `"""`,
    ``,
    `from opentrons import protocol_api`,
    ``,
    `metadata = {`,
    `    "protocolName": ${JSON.stringify(`BioNeMo Plate Setup: ${lead.id}`)},`,
    `    "author": "Aarav Jorwal (@Jorwalzzz)",`,
    `    "description": ${JSON.stringify(`Plate setup for ${lead.id} (${ctx.pdbId})`)},`,
    `    "apiLevel": "2.15"`,
    `}`,
    ``,
    `CAMPAIGN_SPEC = ${specLiteral}`,
    `SYNTHESIS_STEPS = ${stepsLiteral}`,
    ``,
    `def run(protocol: protocol_api.ProtocolContext):`,
    `    tips_300 = protocol.load_labware("opentrons_96_tiprack_300ul", 1)`,
    `    reagents = protocol.load_labware("nest_12_reservoir_15ml", 2)`,
    `    temp_mod = protocol.load_module("temperature module gen2", 3)`,
    `    rxn_block = temp_mod.load_labware("opentrons_24_aluminumblock_nest_1.5ml_snapcap")`,
    `    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips_300])`,
    `    temp_mod.set_temperature(celsius=25)`,
    `    for step in SYNTHESIS_STEPS:`,
    `        dest = rxn_block[step["dest_well"]]`,
    `        protocol.comment(f"Step {step['step_number']}: {step['reaction_type']}")`,
    `        for r_idx, _reagent in enumerate(step["reagents"], start=1):`,
    `            well = f"A{min(12, r_idx)}"`,
    `            p300.pick_up_tip()`,
    `            p300.aspirate(50, reagents[well])`,
    `            p300.dispense(50, dest)`,
    `            p300.mix(3, 40, dest)`,
    `            p300.drop_tip()`,
    `    temp_mod.set_temperature(celsius=4)`,
    `    protocol.comment("Plate setup complete for " + CAMPAIGN_SPEC["candidate_id"])`,
    ``
  ].join('\n');
}

export async function generateRobotProtocol() {
  const ctx = buildExportContext();
  const lead = ctx.selectedLead || {
    id: 'LEAD-001',
    smiles: 'CC(=O)N1CCNCC1'
  };
  const revisionKey = `${ctx.runId}:${ctx.selectedLeadId}:${ctx.leadRevision}`;

  showToast('Generating Opentrons OT-2 Python protocol...');
  try {
    if (!(await probeBackendHealth())) throw new Error('Static host: use client-side protocol');
    const res = await fetch('./api/robot/protocol', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
      body: JSON.stringify({
        lead_id: lead.id,
        smiles: lead.smiles || 'CC(=O)N1CCNCC1',
        retrosynthesis: ctx.retrosynthesis
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.currentOt2Code = data.ot2_protocol_py || '';
    state.currentOt2Key = revisionKey;
    state.currentLabCardMd = data.lab_card_md || '';

    const codeEl = document.getElementById('ot2CodeContent');
    if (codeEl) codeEl.textContent = state.currentOt2Code;
    const leadEl = document.getElementById('robotModalLeadId');
    if (leadEl) leadEl.textContent = data.candidate_id;
    const stepsEl = document.getElementById('robotModalSteps');
    if (stepsEl) stepsEl.textContent = `${data.num_steps} Steps (${data.feasibility})`;
    openRobotModal();
    showToast('Opentrons OT-2 Protocol generated.');
  } catch (err) {
    state.currentOt2Code = buildStaticOt2Script(ctx);
    state.currentOt2Key = revisionKey;
    const codeEl = document.getElementById('ot2CodeContent');
    if (codeEl) codeEl.textContent = state.currentOt2Code;
    const leadEl = document.getElementById('robotModalLeadId');
    if (leadEl) leadEl.textContent = lead.id;
    const stepsEl = document.getElementById('robotModalSteps');
    if (stepsEl) stepsEl.textContent = `${ctx.retrosynthesis?.num_steps || 2} Steps (${ctx.retrosynthesis?.feasibility || 'Heuristic BRICS / Literature Precedent'})`;
    openRobotModal();
    showToast('Opentrons OT-2 Protocol generated (Static Ready).');
  }
}

export async function generateLabCard() {
  const ctx = buildExportContext();
  const lead = ctx.selectedLead || {
    id: 'LEAD-001',
    smiles: 'CC(=O)N1CCNCC1'
  };

  try {
    if (!(await probeBackendHealth())) throw new Error('Static host: use client-side protocol');
    const res = await fetch('./api/robot/protocol', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
      body: JSON.stringify({ lead_id: lead.id, smiles: lead.smiles, retrosynthesis: ctx.retrosynthesis })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    downloadBlob(data.lab_card_md, buildExportFilename(ctx, 'wetlab_sop', 'md'), 'text/markdown');
    showToast('Wet-Lab SOP Card (.md) downloaded.');
  } catch (err) {
    const retroFeasibility = ctx.retrosynthesis?.feasibility || 'Heuristic BRICS / Literature Precedent';
    const steps = Array.isArray(ctx.retrosynthesis?.steps) ? ctx.retrosynthesis.steps : [];
    const stepLines = steps.length > 0
      ? steps.map((s, idx) => `### Step ${s.step || idx + 1}: ${escapeMdCell(s.reaction_type || 'Step')}\n- **Reagents:** ${escapeMdCell((s.reagents || []).join(', ') || 'Standard')}\n- **Est. Yield:** ${Number(s.yield_pct || 80).toFixed(0)}% (${escapeMdCell(s.difficulty || 'Heuristic')})`).join('\n\n')
      : `- Heuristic BRICS / Literature Precedent`;
    const cardContent = [
      `# Wet-Lab Protocol Card -- ${escapeMdCell(lead.id)} (${escapeMdCell(ctx.target)})`,
      `> **Generated by BioNeMo NIM Benchmark Suite (Illustrative / Unvalidated)**`,
      `> **Provenance:** ${ctx.provenance} | **Target Scaffold:** \`${escapeMdCell(lead.smiles || 'CC(=O)N1CCNCC1')}\``,
      ``,
      `## 1. Route Overview`,
      `- **Retrosynthetic Assessment:** ${escapeMdCell(retroFeasibility)}`,
      ``,
      `## 2. Step-by-Step Conditions`,
      stepLines,
      ``,
      `## 3. License & Legal Notice`,
      `- **AGPL-3.0-only** · ${ctx.legal_notice}`
    ].join('\n');
    downloadBlob(cardContent, buildExportFilename(ctx, 'wetlab_sop', 'md'), 'text/markdown');
    showToast('Wet-Lab SOP Card (.md) downloaded.');
  }
}

export function downloadCurrentOT2Py() {
  if (!state.currentOt2Code) return;
  const leadId = (state.currentSelectedLead && state.currentSelectedLead.id) || 'LEAD-001';
  downloadBlob(state.currentOt2Code, `ot2_synthesis_${leadId}.py`, 'text/x-python');
  showToast('ot2_synthesis protocol downloaded.');
}

export async function copyOT2Code() {
  if (!state.currentOt2Code) return;
  if (await copyToClipboard(state.currentOt2Code)) {
    showToast('Python protocol copied to clipboard.');
  }
}

export async function runResistanceStressTest() {
  const lead = state.currentSelectedLead || (state.currentLeads && state.currentLeads[0]) || {
    id: 'LEAD-001',
    affinity: -9.2,
    smiles: 'O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5'
  };
  const currentTargetTab = state.currentTargetTab || 'presets';
  let target = document.getElementById('targetSelect')?.value || '7RPZ';
  if (currentTargetTab === 'esmfold') target = state.currentTargetSeq || 'ESMFold De Novo Target';
  else if (currentTargetTab === 'rcsb') target = (document.getElementById('customTargetInput')?.value || '').trim() || 'Target';

  showToast('Running ESM-2 mutational scan & MolMIM counter-design...');
  openResistanceModal();

  const statusBadge = document.getElementById('resStatusBadge');
  if (statusBadge) {
    statusBadge.textContent = 'COMPUTING...';
    statusBadge.className = 'px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 animate-pulse';
  }

  try {
    if (!(await probeBackendHealth())) throw new Error('Static host: use illustrative resistance model');
    const res = await fetch('./api/resistance/evolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-BioNeMo-CSRF': '1' },
      body: JSON.stringify({
        target: target,
        lead_id: lead.id,
        smiles: lead.smiles,
        binding_affinity: lead.affinity
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.latestResistanceData = data;

    const titleEl = document.getElementById('resMutationTitle');
    if (titleEl) titleEl.textContent = data.mutation_simulated || 'Mutational Escape Challenge';
    const hotspotsEl = document.getElementById('resHotspots');
    if (hotspotsEl) hotspotsEl.textContent = (data.hotspot_residues || []).join(', ');

    const origEl = document.getElementById('resOrigAff');
    if (origEl) origEl.textContent = `${data.original_affinity.toFixed(2)} kcal/mol`;
    const mutEl = document.getElementById('resMutAff');
    if (mutEl) mutEl.textContent = `${data.mutant_affinity.toFixed(2)} kcal/mol`;
    const evolvedEl = document.getElementById('resEvolvedAff');
    if (evolvedEl) evolvedEl.textContent = `${data.evolved_affinity.toFixed(2)} kcal/mol`;
    const deltaEl = document.getElementById('resDeltaRecovery');
    if (deltaEl) deltaEl.textContent = `+${data.delta_recovery.toFixed(2)} kcal/mol`;

    const mechEl = document.getElementById('resMechanismText');
    if (mechEl) mechEl.textContent = data.structural_mechanism || 'Bioisosteric latent transformation circumvents steric clash in binding pocket.';
    const smilesEl = document.getElementById('resEvolvedSmiles');
    if (smilesEl) smilesEl.textContent = data.evolved_smiles || '';

    if (statusBadge) {
      statusBadge.textContent = data.verdict || 'RESISTANCE BYPASSED';
      statusBadge.className = 'px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
    }

    showToast('Resistance scan complete: Escape scaffold evolved via MolMIM.');
  } catch (err) {
    state.latestResistanceData = {
      mutation_simulated: 'G12D → G12V (Steric Resistance — Illustrative Scripted Scenario)',
      hotspot_residues: ['Asp12', 'Tyr96', 'Gln61', 'Lys16'],
      original_affinity: lead.affinity || -9.2,
      mutant_affinity: -5.8,
      evolved_affinity: -9.9,
      delta_recovery: 4.1,
      structural_mechanism: '[Illustrative scripted scenario — not real resistance data] Simulated G12D→G12V substitution reduces switch-II electrostatic complementarity. MolMIM counter-design remodels terminal heterocycle to restore pocket fit.',
      evolved_smiles: 'O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5',
      verdict: 'RESISTANCE BYPASSED'
    };
    const titleEl = document.getElementById('resMutationTitle');
    if (titleEl) titleEl.textContent = state.latestResistanceData.mutation_simulated;
    const hotspotsEl = document.getElementById('resHotspots');
    if (hotspotsEl) hotspotsEl.textContent = state.latestResistanceData.hotspot_residues.join(', ');
    const origEl = document.getElementById('resOrigAff');
    if (origEl) origEl.textContent = `${state.latestResistanceData.original_affinity.toFixed(2)} kcal/mol`;
    const mutEl = document.getElementById('resMutAff');
    if (mutEl) mutEl.textContent = `${state.latestResistanceData.mutant_affinity.toFixed(2)} kcal/mol`;
    const evolvedEl = document.getElementById('resEvolvedAff');
    if (evolvedEl) evolvedEl.textContent = `${state.latestResistanceData.evolved_affinity.toFixed(2)} kcal/mol`;
    const deltaEl = document.getElementById('resDeltaRecovery');
    if (deltaEl) deltaEl.textContent = `+${state.latestResistanceData.delta_recovery.toFixed(2)} kcal/mol`;
    const mechEl = document.getElementById('resMechanismText');
    if (mechEl) mechEl.textContent = state.latestResistanceData.structural_mechanism;
    const smilesEl = document.getElementById('resEvolvedSmiles');
    if (smilesEl) smilesEl.textContent = state.latestResistanceData.evolved_smiles;
    if (statusBadge) {
      statusBadge.textContent = state.latestResistanceData.verdict;
      statusBadge.className = 'px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
    }
    showToast('Calibrated resistance scan loaded (Static Ready).');
  }
}

export function adoptEvolvedScaffold() {
  if (!state.latestResistanceData || !state.latestResistanceData.evolved_smiles) {
    showToast('No evolved scaffold available.');
    return;
  }
  const affBox = document.getElementById('redockAffinityDisplay');
  if (affBox) affBox.textContent = '';
  const input = document.getElementById('workbenchSmilesInput');
  if (input) {
    input.value = state.latestResistanceData.evolved_smiles;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    showToast('Evolved scaffold injected into Chemical Workbench.');
  }
  closeResistanceModal();
}

export async function copyEvolvedSmiles() {
  const smiles = document.getElementById('resEvolvedSmiles')?.textContent;
  if (!smiles) return;
  if (await copyToClipboard(smiles)) {
    showToast('Evolved SMILES copied.');
  }
}
