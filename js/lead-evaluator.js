/**
 * BioNeMo NIM Inference Benchmark - Lead Candidate Evaluator & Pareto Scatter
 * Module: ./js/lead-evaluator.js
 * 
 * Implements:
 * 1. Unclipped lead candidate matrix with non-wrapping monospace IDs.
 * 2. Distinct DiffDock screening score (-4.81 kcal/mol) vs MM-GBSA rescore (-10.82 kcal/mol).
 * 3. Custom Retina SVG Pareto Scatter plot (Affinity vs. QED, radius by SAScore, Pareto curve).
 * 4. Bidirectional hover/click synchronization between table rows and scatter points.
 * 5. In-browser Drag-and-Drop CSV / JSON parser with instant re-rendering.
 */

(function () {
  'use strict';

  // Security & Upload DoS Guard limits
  const MAX_FILE_BYTES = 5 * 1024 * 1024; // 5 MB
  const MAX_ROWS = 5000;

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Ground-truth dataset from results/screened_candidates_summary.csv & DOSSIER
  const DEFAULT_CANDIDATES = [
    {
      id: "NIM-LEAD-01-03",
      smiles: "O=C(N1CCN(C2=NC=C(F)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5",
      affinity: -4.81,
      mmgbsa: -10.82,
      confidence: 0.98,
      qed: 0.309,
      mw: 531.51,
      logp: 5.55,
      sascore: 7.74,
      pains: 0,
      ro5Violations: 2,
      isPareto: true,
      verdict: "PARETO OPTIMAL"
    },
    {
      id: "NIM-LEAD-01-01",
      smiles: "O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5",
      affinity: -4.80,
      mmgbsa: -10.45,
      confidence: 0.98,
      qed: 0.297,
      mw: 547.97,
      logp: 6.07,
      sascore: 7.85,
      pains: 0,
      ro5Violations: 2,
      isPareto: false,
      verdict: "SCREENING HIT"
    },
    {
      id: "NIM-LEAD-01-04",
      smiles: "CC1CN(CCN1)C(=O)C2=C(N)N=C3C(F)=CC=CC3=C2C4=NC=C(Cl)C5=C4C(C6=C(F)C=CC=C6F)=CC=C5",
      affinity: -4.56,
      mmgbsa: -10.12,
      confidence: 0.98,
      qed: 0.274,
      mw: 562.00,
      logp: 6.20,
      sascore: 7.90,
      pains: 0,
      ro5Violations: 2,
      isPareto: false,
      verdict: "SCREENING HIT"
    },
    {
      id: "NIM-LEAD-01-02",
      smiles: "O=C(N1CCN(C2=NC=C(Cl)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(Cl)=CC=CC6=C5",
      affinity: -3.95,
      mmgbsa: -9.65,
      confidence: 0.98,
      qed: 0.268,
      mw: 564.42,
      logp: 6.58,
      sascore: 7.96,
      pains: 0,
      ro5Violations: 2,
      isPareto: false,
      verdict: "BORDERLINE"
    }
  ];

  let currentCandidates = [...DEFAULT_CANDIDATES];
  let hoveredCandidateId = null;

  // DOM elements cache
  let tableBodyEl = null;
  let paretoContainerEl = null;
  let dropzoneEl = null;
  let fileInputEl = null;
  let btnSampleBatch = null;

  /**
   * Calculate Multi-Objective Pareto Frontier (Max Affinity / Min deltaG & Max QED)
   */
  function computeParetoFrontier(candidates) {
    const sorted = [...candidates].sort((a, b) => a.affinity - b.affinity); // Most negative deltaG first
    const frontier = [];
    let maxQedSoFar = -Infinity;

    sorted.forEach((c) => {
      if (c.qed > maxQedSoFar) {
        c.isPareto = true;
        frontier.push(c);
        maxQedSoFar = c.qed;
      } else {
        c.isPareto = false;
      }
    });

    return frontier;
  }

  /**
   * Render Custom Retina SVG Pareto Scatter Plot
   */
  function renderParetoScatter(container, candidates) {
    if (!container || !candidates || candidates.length === 0) return;

    const width = 480;
    const height = 360;
    const padding = { top: 30, right: 30, bottom: 50, left: 60 };
    const plotW = width - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;

    // Extents
    const affinities = candidates.map(c => c.affinity);
    const qeds = candidates.map(c => c.qed);

    const minAffinity = Math.min(-5.2, Math.min(...affinities) - 0.2);
    const maxAffinity = Math.max(-3.5, Math.max(...affinities) + 0.2);
    const minQed = Math.max(0.15, Math.min(...qeds) - 0.05);
    const maxQed = Math.min(0.60, Math.max(...qeds) + 0.05);

    function scaleX(aff) {
      // More negative (stronger binding) on left
      return padding.left + ((aff - minAffinity) / (maxAffinity - minAffinity)) * plotW;
    }

    function scaleY(q) {
      // Higher QED (better drug-likeness) on top
      return height - padding.bottom - ((q - minQed) / (maxQed - minQed)) * plotH;
    }

    // Sort Pareto points to form curve
    const paretoPoints = candidates.filter(c => c.isPareto).sort((a, b) => a.affinity - b.affinity);

    let curvePath = '';
    if (paretoPoints.length > 1) {
      curvePath = `M ${scaleX(paretoPoints[0].affinity)} ${scaleY(paretoPoints[0].qed)} ` +
        paretoPoints.slice(1).map(p => `L ${scaleX(p.affinity)} ${scaleY(p.qed)}`).join(' ');
    }

    let svgHtml = `
      <svg class="pareto-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Pareto Scatter Plot: Binding Affinity vs. QED">
        <!-- Axes Grid Lines -->
        <g class="grid-group">
    `;

    // Horizontal grid ticks (QED)
    const yTicks = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45];
    yTicks.forEach(tick => {
      if (tick >= minQed && tick <= maxQed) {
        const y = scaleY(tick);
        svgHtml += `
          <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" class="pareto-axis-grid" />
          <text x="${padding.left - 8}" y="${y + 3}" class="pareto-axis-text" text-anchor="end">${tick.toFixed(2)}</text>
        `;
      }
    });

    // Vertical grid ticks (Affinity deltaG)
    const xTicks = [-5.0, -4.5, -4.0, -3.5];
    xTicks.forEach(tick => {
      if (tick >= minAffinity && tick <= maxAffinity) {
        const x = scaleX(tick);
        svgHtml += `
          <line x1="${x}" y1="${padding.top}" x2="${x}" y2="${height - padding.bottom}" class="pareto-axis-grid" />
          <text x="${x}" y="${height - padding.bottom + 18}" class="pareto-axis-text" text-anchor="middle">${tick.toFixed(1)}</text>
        `;
      }
    });

    svgHtml += `
        <!-- Axes Lines -->
        <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" class="pareto-axis-line" stroke-width="1.5" />
        <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" class="pareto-axis-line" stroke-width="1.5" />

        <!-- Axis Labels -->
        <text x="${padding.left + plotW / 2}" y="${height - 12}" font-family="var(--font-mono)" font-size="11" fill="var(--color-ink-secondary)" text-anchor="middle">
          Binding Affinity &Delta;G (kcal/mol) &larr; Stronger
        </text>
        <text x="18" y="${padding.top + plotH / 2}" font-family="var(--font-mono)" font-size="11" fill="var(--color-ink-secondary)" text-anchor="middle" transform="rotate(-90 18 ${padding.top + plotH / 2})">
          Drug-Likeness (QED) &rarr;
        </text>
      </g>
    `;

    // Pareto Curve
    if (curvePath) {
      svgHtml += `<path d="${curvePath}" class="pareto-curve" />`;
    }

    // Points
    svgHtml += `<g class="points-group">`;
    candidates.forEach(c => {
      const cx = scaleX(c.affinity);
      const cy = scaleY(c.qed);
      // Scale radius by SAScore: 7.7 -> ~6px, 4.8 -> ~8px
      const r = Math.max(5, Math.min(9, 14 - c.sascore));
      const color = c.isPareto ? 'var(--color-signal-green)' : '#F59E0B';
      const isHovered = hoveredCandidateId === c.id;

      const safeId = escapeHtml(c.id);
      const safeLabel = escapeHtml(`${c.id}: ${c.affinity} kcal/mol, QED ${c.qed}`);
      const cleanShortId = escapeHtml(c.id.replace('NIM-LEAD-', ''));

      svgHtml += `
        <circle
          cx="${cx.toFixed(1)}"
          cy="${cy.toFixed(1)}"
          r="${isHovered ? 9 : r}"
          fill="${color}"
          class="pareto-point ${isHovered ? 'highlighted' : ''}"
          data-id="${safeId}"
          tabindex="0"
          role="button"
          aria-label="${safeLabel}"
        />
        <text x="${(cx + 8).toFixed(1)}" y="${(cy - 6).toFixed(1)}" font-family="var(--font-mono)" font-size="9" fill="${color}" font-weight="${c.isPareto ? '700' : '400'}">
          ${cleanShortId}
        </text>
      `;
    });
    svgHtml += `</g></svg>`;

    container.innerHTML = svgHtml;

    // Attach Point Listeners
    const points = container.querySelectorAll('.pareto-point');
    points.forEach(pt => {
      const id = pt.getAttribute('data-id');
      pt.addEventListener('mouseenter', () => {
        setHoveredCandidate(id);
      });
      pt.addEventListener('mouseleave', () => {
        setHoveredCandidate(null);
      });
    });
  }

  /**
   * Render Lead Candidates Table (Zero-Clipping, Strict Monospace IDs)
   */
  function renderLeadTable(tbody, candidates) {
    if (!tbody || !candidates) return;

    let html = '';
    candidates.forEach(c => {
      const isHovered = hoveredCandidateId === c.id;
      const paretoBadge = c.isPareto
        ? `<span class="badge-measured" style="font-weight:700;">★ PARETO</span>`
        : `<span style="font-family:var(--font-mono);font-size:0.75rem;color:var(--color-ink-muted);">Standard</span>`;

      const ro5Badge = c.ro5Violations === 0
        ? `<span style="color:var(--color-signal-green);font-weight:600;">Pass (0)</span>`
        : `<span style="color:#F59E0B;font-weight:600;">${c.ro5Violations} Alerts</span>`;

      const safeId = escapeHtml(c.id);
      const safeSmiles = escapeHtml(c.smiles);

      html += `
        <tr class="${isHovered ? 'highlighted' : ''}" data-id="${safeId}">
          <td class="lead-id-cell">
            ${safeId}
          </td>
          <td style="max-width:180px;">
            <div style="font-family:var(--font-mono);font-size:0.72rem;color:var(--color-ink-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${safeSmiles}">
              ${safeSmiles}
            </div>
          </td>
          <td class="lead-score-cell" style="color:var(--color-signal-green);">
            ${c.affinity.toFixed(2)}
          </td>
          <td class="lead-score-cell" style="color:#5CE1FF;">
            ${c.mmgbsa ? c.mmgbsa.toFixed(2) : '-'}
          </td>
          <td class="lead-score-cell">
            ${c.qed.toFixed(3)}
          </td>
          <td class="lead-score-cell">
            ${c.sascore.toFixed(2)}
          </td>
          <td style="font-family:var(--font-mono);font-size:0.75rem;white-space:nowrap;">
            ${c.mw.toFixed(1)} / ${c.logp.toFixed(2)}
          </td>
          <td>${ro5Badge}</td>
          <td>${paretoBadge}</td>
        </tr>
      `;
    });

    tbody.innerHTML = html;

    // Attach Row Listeners
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(r => {
      const id = r.getAttribute('data-id');
      r.addEventListener('mouseenter', () => {
        setHoveredCandidate(id);
      });
      r.addEventListener('mouseleave', () => {
        setHoveredCandidate(null);
      });
    });
  }

  function setHoveredCandidate(id) {
    hoveredCandidateId = id;
    if (tableBodyEl) {
      const rows = tableBodyEl.querySelectorAll('tr');
      rows.forEach(r => {
        r.classList.toggle('highlighted', r.getAttribute('data-id') === id);
      });
    }
    if (paretoContainerEl) {
      const points = paretoContainerEl.querySelectorAll('.pareto-point');
      points.forEach(p => {
        p.classList.toggle('highlighted', p.getAttribute('data-id') === id);
      });
    }
  }

  /**
   * Parse Client-Side CSV / JSON Upload
   */
  function handleFile(file) {
    if (!file) return;

    if (file.size > MAX_FILE_BYTES) {
      alert(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds maximum allowed limit of 5 MB.`);
      return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const text = e.target.result;
        let parsed = [];

        if (file.name.endsWith('.json')) {
          const raw = JSON.parse(text);
          let items = Array.isArray(raw) ? raw : (raw.candidates || raw.leads || []);
          if (items.length > MAX_ROWS) {
            alert(`File contains ${items.length} records. Limiting to first ${MAX_ROWS} candidates to prevent UI freezing.`);
            items = items.slice(0, MAX_ROWS);
          }
          parsed = items.map((c, i) => ({
            id: String(c.id || `LEAD-${i + 1}`).trim(),
            smiles: String(c.smiles || 'C').trim(),
            affinity: parseFloat(c.affinity) || -4.5,
            mmgbsa: c.mmgbsa ? parseFloat(c.mmgbsa) : -10.0,
            qed: c.qed != null ? parseFloat(c.qed) : 0.35,
            mw: c.mw != null ? parseFloat(c.mw) : 500,
            logp: c.logp != null ? parseFloat(c.logp) : 5.0,
            sascore: c.sascore != null ? parseFloat(c.sascore) : 6.0,
            pains: c.pains != null ? parseInt(c.pains, 10) : 0,
            ro5Violations: c.ro5Violations != null ? parseInt(c.ro5Violations, 10) : 1,
            verdict: String(c.verdict || 'CUSTOM UPLOAD').trim()
          }));
        } else {
          // Parse CSV
          let lines = text.trim().split(/\r?\n/);
          if (lines.length < 2) throw new Error("CSV has insufficient rows.");
          const totalRows = lines.length - 1;
          if (totalRows > MAX_ROWS) {
            alert(`CSV contains ${totalRows} data rows. Limiting to first ${MAX_ROWS} candidates to prevent UI freezing.`);
            lines = lines.slice(0, MAX_ROWS + 1);
          }
          const headers = lines[0].split(',').map(h => h.trim());

          for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
            if (cols.length >= 4) {
              parsed.push({
                id: cols[0] || `LEAD-${i}`,
                smiles: cols[1] || 'C',
                affinity: parseFloat(cols[2]) || -4.5,
                mmgbsa: cols[3] ? parseFloat(cols[3]) : -10.0,
                qed: cols[4] ? parseFloat(cols[4]) : 0.35,
                mw: cols[5] ? parseFloat(cols[5]) : 500,
                logp: cols[6] ? parseFloat(cols[6]) : 5.0,
                sascore: cols[7] ? parseFloat(cols[7]) : 6.0,
                ro5Violations: 1,
                verdict: "CUSTOM UPLOAD"
              });
            }
          }
        }

        if (parsed.length > 0) {
          computeParetoFrontier(parsed);
          currentCandidates = parsed;
          renderLeadTable(tableBodyEl, currentCandidates);
          renderParetoScatter(paretoContainerEl, currentCandidates);
          console.log(`[Lead Evaluator] Loaded ${parsed.length} custom candidates.`);
        }
      } catch (err) {
        alert("Failed to parse file: " + err.message);
      }
    };

    reader.readAsText(file);
  }

  function init() {
    tableBodyEl = document.getElementById('lead-matrix-body');
    paretoContainerEl = document.getElementById('pareto-scatter-container');
    dropzoneEl = document.getElementById('lead-dropzone');
    fileInputEl = document.getElementById('lead-file-input');
    btnSampleBatch = document.getElementById('btn-load-sample-batch');

    // Compute initial Pareto Frontier
    computeParetoFrontier(currentCandidates);

    // Initial renders
    if (tableBodyEl) renderLeadTable(tableBodyEl, currentCandidates);
    if (paretoContainerEl) renderParetoScatter(paretoContainerEl, currentCandidates);

    // Dropzone Listeners
    if (dropzoneEl) {
      dropzoneEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzoneEl.classList.add('drag-active');
      });
      dropzoneEl.addEventListener('dragleave', () => {
        dropzoneEl.classList.remove('drag-active');
      });
      dropzoneEl.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzoneEl.classList.remove('drag-active');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          handleFile(e.dataTransfer.files[0]);
        }
      });
    }

    if (fileInputEl) {
      fileInputEl.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          handleFile(e.target.files[0]);
        }
      });
    }

    if (btnSampleBatch) {
      btnSampleBatch.addEventListener('click', (e) => {
        e.preventDefault();
        currentCandidates = [...DEFAULT_CANDIDATES];
        computeParetoFrontier(currentCandidates);
        renderLeadTable(tableBodyEl, currentCandidates);
        renderParetoScatter(paretoContainerEl, currentCandidates);
      });
    }
  }

  // Bind to DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Global namespace
  window.BioNeMoEvaluator = {
    getCandidates: () => currentCandidates,
    loadCandidates: (list) => {
      currentCandidates = list;
      computeParetoFrontier(currentCandidates);
      renderLeadTable(tableBodyEl, currentCandidates);
      renderParetoScatter(paretoContainerEl, currentCandidates);
    }
  };
})();
