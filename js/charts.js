/**
 * BioNeMo NIM Inference Benchmark - Log-Scale Dumbbell Chart & Matrix Drawer
 * Module: ./js/charts.js
 * 
 * Implements:
 * 1. Logarithmic Dumbbell Plot (0.05s to 200s) comparing AMD EPYC 7763 vs NVIDIA H100 SXM5.
 * 2. Precision hover tooltips with output parity metrics (RMSD, Cosine Similarity).
 * 3. Collapsible Telemetry Matrix Drawer with real-time text filter and model pills.
 * 4. Sortable table columns and one-click CSV / JSON export engines.
 */

import { escapeHtml, toCsvCell, downloadBlob } from './shared/dom-utils.js';

  let benchmarkData = null;
  let activeFilter = 'all';
  let searchTerm = '';
  let sortColumn = 'speedup_multiplier';
  let sortAscending = false;
  let listenersBound = false;

  // Logarithmic scale parameters (0.05s to 200s)
  const MIN_VAL = 0.05;
  const MAX_VAL = 200.0;
  const LOG_MIN = Math.log10(MIN_VAL);
  const LOG_MAX = Math.log10(MAX_VAL);
  const LOG_RANGE = LOG_MAX - LOG_MIN;

  const AXIS_TICKS = [
    { val: 0.05, label: "0.05s" },
    { val: 0.1, label: "0.1s" },
    { val: 0.5, label: "0.5s" },
    { val: 1.0, label: "1.0s" },
    { val: 5.0, label: "5.0s" },
    { val: 10.0, label: "10s" },
    { val: 50.0, label: "50s" },
    { val: 100.0, label: "100s" },
    { val: 200.0, label: "200s" }
  ];

  function getXPos(val, startX, plotWidth) {
    const clamped = Math.max(MIN_VAL, Math.min(MAX_VAL, val));
    const logVal = Math.log10(clamped);
    const fraction = (logVal - LOG_MIN) / LOG_RANGE;
    return startX + fraction * plotWidth;
  }

  /**
   * Render SVG Log-scale Dumbbell Chart
   */
  function renderDumbbellChart(container, benchmarks) {
    if (!container || !benchmarks || benchmarks.length === 0) return;

    const svgWidth = 860;
    const rowHeight = 54;
    const topMargin = 50;
    const bottomMargin = 40;
    const svgHeight = topMargin + benchmarks.length * rowHeight + bottomMargin;

    const startX = 220; // Room for left labels
    const endX = 740;   // Room for right speedup badges
    const plotWidth = endX - startX;

    let svgHtml = `
      <svg class="dumbbell-svg" viewBox="0 0 ${svgWidth} ${svgHeight}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Log-scale latency dumbbell chart">
        <defs>
          <linearGradient id="tether-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#10B981" />
            <stop offset="100%" stop-color="#FF8A4C" />
          </linearGradient>
        </defs>

        <!-- Background Axis Lines & Ticks -->
        <g class="axis-group">
    `;

    // Draw vertical log tick lines
    AXIS_TICKS.forEach((tick) => {
      const x = getXPos(tick.val, startX, plotWidth);
      svgHtml += `
        <line x1="${x.toFixed(1)}" y1="${topMargin - 15}" x2="${x.toFixed(1)}" y2="${svgHeight - bottomMargin + 10}" class="dumbbell-axis-line" />
        <text x="${x.toFixed(1)}" y="${topMargin - 22}" class="dumbbell-axis-text">${tick.label}</text>
      `;
    });

    svgHtml += `</g><g class="rows-group">`;

    // Draw Rows
    benchmarks.forEach((b, idx) => {
      const y = topMargin + idx * rowHeight + rowHeight / 2;
      const xGpu = getXPos(b.gpu_latency_s, startX, plotWidth);
      const xCpu = getXPos(b.cpu_latency_s, startX, plotWidth);

      svgHtml += `
        <g class="dumbbell-row" data-id="${b.id}" tabindex="0" role="button" aria-label="${b.nim_service}: GPU ${b.gpu_latency_s}s, CPU ${b.cpu_latency_s}s, ${b.speedup_multiplier}x">
          <!-- Row Hover Backdrop -->
          <rect x="10" y="${y - rowHeight / 2 + 4}" width="${svgWidth - 20}" height="${rowHeight - 8}" rx="6" fill="rgba(255,255,255,0.02)" class="row-hover-bg" />

          <!-- Left Labels -->
          <text x="20" y="${y - 4}" class="dumbbell-label">${b.nim_service}</text>
          <text x="20" y="${y + 13}" class="dumbbell-sublabel">${b.target_complex}</text>

          <!-- Tether Line -->
          <line x1="${xGpu.toFixed(1)}" y1="${y}" x2="${xCpu.toFixed(1)}" y2="${y}" stroke="url(#tether-grad)" class="dumbbell-tether" />

          <!-- GPU Node (Green) -->
          <circle cx="${xGpu.toFixed(1)}" cy="${y}" r="6" class="dumbbell-point-gpu" />
          <text x="${xGpu.toFixed(1)}" y="${y + 20}" font-family="var(--font-mono)" font-size="10" fill="var(--color-signal-green)" text-anchor="middle">${b.gpu_latency_s >= 1 ? b.gpu_latency_s.toFixed(2) : b.gpu_latency_s.toFixed(3)}s</text>

          <!-- CPU Node (Ember) -->
          <circle cx="${xCpu.toFixed(1)}" cy="${y}" r="6" class="dumbbell-point-cpu" />
          <text x="${xCpu.toFixed(1)}" y="${y + 20}" font-family="var(--font-mono)" font-size="10" fill="#FF8A4C" text-anchor="middle">${b.cpu_latency_s.toFixed(1)}s</text>

          <!-- Right Speedup Badge -->
          <text x="${svgWidth - 20}" y="${y + 4}" class="dumbbell-speedup-text">${b.speedup_multiplier.toFixed(1)}x</text>
        </g>
      `;
    });

    svgHtml += `</g></svg>`;
    container.innerHTML = svgHtml;

    // Attach Row Tooltips / Click detail alerts
    const rows = container.querySelectorAll('.dumbbell-row');
    rows.forEach((row) => {
      const id = row.getAttribute('data-id');
      const item = benchmarks.find(b => b.id === id);
      if (!item) return;

      row.addEventListener('mouseenter', (e) => showChartTooltip(e, item));
      row.addEventListener('mousemove', (e) => positionChartTooltip(e));
      row.addEventListener('mouseleave', hideChartTooltip);
      row.addEventListener('focus', () => {
        const rect = row.getBoundingClientRect();
        showChartTooltip({ clientX: rect.left + rect.width * 0.5, clientY: rect.top + 10 }, item);
      });
      row.addEventListener('blur', hideChartTooltip);
      row.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const rect = row.getBoundingClientRect();
          showChartTooltip({ clientX: rect.left + rect.width * 0.5, clientY: rect.top + 10 }, item);
        }
      });
    });
  }

  // Floating precision tooltip element
  let tooltipEl = null;

  function ensureTooltip() {
    if (!tooltipEl) {
      tooltipEl = document.createElement('div');
      tooltipEl.className = 'dumbbell-tooltip';
      tooltipEl.style.cssText = `
        position: fixed;
        z-index: 1000;
        pointer-events: none;
        background: var(--color-surface-elevated);
        border: 1px solid var(--color-signal-green);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        font-family: var(--font-body);
        font-size: 0.8rem;
        color: var(--color-ink-primary);
        display: none;
        max-width: 320px;
        backdrop-filter: blur(10px);
      `;
      document.body.appendChild(tooltipEl);
    }
  }

  function showChartTooltip(e, item) {
    ensureTooltip();
    tooltipEl.innerHTML = `
      <div style="font-family:var(--font-display);font-weight:700;font-size:0.95rem;color:var(--color-ink-primary);margin-bottom:0.25rem;">
        ${escapeHtml(item.nim_service)} &mdash; ${escapeHtml(item.target_complex)}
      </div>
      <div style="font-family:var(--font-mono);font-size:0.75rem;color:var(--color-ink-muted);margin-bottom:0.5rem;">
        Task: ${escapeHtml(item.task_type)}
      </div>
      <div style="display:flex;justify-content:space-between;gap:1rem;margin-bottom:0.25rem;font-family:var(--font-mono);">
        <span style="color:var(--color-signal-green);">H100 SXM5: <strong>${item.gpu_latency_s}s</strong></span>
        <span style="color:#FF8A4C;">EPYC 7763: <strong>${item.cpu_latency_s}s</strong></span>
      </div>
      <div style="font-family:var(--font-mono);font-size:0.75rem;color:var(--color-signal-green);font-weight:700;margin-bottom:0.4rem;">
        Acceleration: ${item.speedup_multiplier}x
      </div>
      <div style="font-size:0.75rem;color:var(--color-ink-secondary);border-top:1px solid var(--border-hairline);padding-top:0.35rem;">
        Output Parity: ${escapeHtml(item.output_parity_metric)}
      </div>
    `;
    tooltipEl.style.display = 'block';
    positionChartTooltip(e);
  }

  function positionChartTooltip(e) {
    if (!tooltipEl) return;
    const x = e.clientX + 15;
    const y = e.clientY + 15;
    tooltipEl.style.left = `${Math.min(window.innerWidth - 340, x)}px`;
    tooltipEl.style.top = `${y}px`;
  }

  function hideChartTooltip() {
    if (tooltipEl) tooltipEl.style.display = 'none';
  }

  /**
   * Render Telemetry Matrix Table
   */
  function renderMatrixTable(tbody, benchmarks) {
    if (!tbody || !benchmarks) return;

    // Filter
    let filtered = benchmarks.filter((b) => {
      const matchesFilter = (activeFilter === 'all') ||
        b.nim_service.toLowerCase().includes(activeFilter.toLowerCase()) ||
        b.id.toLowerCase().includes(activeFilter.toLowerCase());

      const query = searchTerm.toLowerCase();
      const matchesSearch = !searchTerm ||
        b.target_complex.toLowerCase().includes(query) ||
        b.nim_service.toLowerCase().includes(query) ||
        b.task_type.toLowerCase().includes(query) ||
        b.uniprot_id.toLowerCase().includes(query);

      return matchesFilter && matchesSearch;
    });

    // Sort
    filtered.sort((a, b) => {
      let valA = a[sortColumn];
      let valB = b[sortColumn];
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortAscending ? -1 : 1;
      if (valA > valB) return sortAscending ? 1 : -1;
      return 0;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center;padding:2rem;color:var(--color-ink-muted);font-family:var(--font-mono);">
            No benchmark records match query "${escapeHtml(searchTerm)}".
          </td>
        </tr>
      `;
      return;
    }

    let rowsHtml = '';
    filtered.forEach((b) => {
      rowsHtml += `
        <tr>
          <td style="font-weight:600;">
            ${escapeHtml(b.nim_service)}
            <div style="font-size:0.75rem;color:var(--color-ink-muted);font-family:var(--font-mono);">${escapeHtml(b.nim_container)}</div>
          </td>
          <td>
            ${escapeHtml(b.target_complex)}
            <div style="font-size:0.75rem;color:var(--color-ink-muted);font-family:var(--font-mono);">${escapeHtml(b.uniprot_id)} (${escapeHtml(b.input_spec)})</div>
          </td>
          <td style="font-size:0.8rem;color:var(--color-ink-secondary);">${escapeHtml(b.task_type)}</td>
          <td class="matrix-td-mono" style="color:#FF8A4C;font-weight:600;">${b.cpu_latency_s.toFixed(2)}s</td>
          <td class="matrix-td-mono" style="color:var(--color-signal-green);font-weight:600;">${b.gpu_latency_s.toFixed(3)}s</td>
          <td class="matrix-td-mono">
            <span class="badge-measured" style="font-weight:700;">${b.speedup_multiplier.toFixed(1)}x</span>
          </td>
          <td style="font-size:0.75rem;color:var(--color-ink-muted);font-family:var(--font-mono);">${escapeHtml(b.output_parity_metric)}</td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;
  }

  /**
   * Export Utilities (CSV & JSON)
   */
  function exportCSV(benchmarks) {
    const headers = ["ID", "Target Complex", "UniProt", "NIM Service", "Task Type", "CPU Latency (s)", "H100 GPU Latency (s)", "Speedup Multiplier", "Output Parity"];
    const rows = (benchmarks || []).map(b => [
      toCsvCell(b.id),
      toCsvCell(b.target_complex),
      toCsvCell(b.uniprot_id),
      toCsvCell(b.nim_service),
      toCsvCell(b.task_type),
      toCsvCell(b.cpu_latency_s),
      toCsvCell(b.gpu_latency_s),
      toCsvCell(b.speedup_multiplier),
      toCsvCell(b.output_parity_metric)
    ]);

    const csvContent = [headers.map(toCsvCell).join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadBlob(csvContent, 'bionemo_benchmark_summary.csv', 'text/csv;charset=utf-8;');
  }

  function exportJSON(data) {
    const jsonStr = JSON.stringify(data, null, 2);
    downloadBlob(jsonStr, 'bionemo_benchmark_summary.json', 'application/json;charset=utf-8;');
  }

  function bindEventListeners() {
    if (listenersBound) return;
    listenersBound = true;

    const drawerHeader = document.getElementById('drawer-header');
    const drawerChevron = document.getElementById('drawer-chevron');
    const drawerContent = document.getElementById('drawer-content');

    if (drawerHeader && drawerContent) {
      drawerHeader.addEventListener('click', () => {
        const isOpen = drawerContent.classList.toggle('open');
        drawerHeader.classList.toggle('open', isOpen);
        drawerHeader.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        if (drawerChevron) drawerChevron.classList.toggle('open', isOpen);
      });
    }

    const searchInput = document.getElementById('table-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        searchTerm = e.target.value;
        const tbody = document.getElementById('matrix-table-body');
        if (tbody && benchmarkData) renderMatrixTable(tbody, benchmarkData.benchmarks || []);
      });
    }

    const filterPills = document.querySelectorAll('.matrix-filter-pill');
    filterPills.forEach((pill) => {
      pill.addEventListener('click', () => {
        filterPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        activeFilter = pill.getAttribute('data-filter') || 'all';
        const tbody = document.getElementById('matrix-table-body');
        if (tbody && benchmarkData) renderMatrixTable(tbody, benchmarkData.benchmarks || []);
      });
    });

    const sortHeaders = document.querySelectorAll('.sortable-th');
    sortHeaders.forEach((th) => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        if (sortColumn === col) {
          sortAscending = !sortAscending;
        } else {
          sortColumn = col;
          sortAscending = false;
        }
        const tbody = document.getElementById('matrix-table-body');
        if (tbody && benchmarkData) renderMatrixTable(tbody, benchmarkData.benchmarks || []);
      });
    });

    const btnCsv = document.getElementById('btn-export-csv');
    const btnJson = document.getElementById('btn-export-json');

    if (btnCsv) {
      btnCsv.addEventListener('click', () => {
        if (benchmarkData) exportCSV(benchmarkData.benchmarks || []);
      });
    }
    if (btnJson) {
      btnJson.addEventListener('click', () => {
        if (benchmarkData) exportJSON(benchmarkData);
      });
    }
  }

  function setupComponent() {
    const data = window.BioNeMoData || (window.BioNeMoHydrator ? window.BioNeMoHydrator.getFallbackData() : null);
    if (!data) return;

    benchmarkData = data;
    const benchmarks = data.benchmarks || [];

    const chartContainer = document.getElementById('dumbbell-chart-container');
    if (chartContainer) {
      renderDumbbellChart(chartContainer, benchmarks);
    }

    const tbody = document.getElementById('matrix-table-body');
    if (tbody) {
      renderMatrixTable(tbody, benchmarks);
    }

    bindEventListeners();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupComponent);
  } else {
    setupComponent();
  }

  window.addEventListener('bionemo:data-ready', (e) => {
    benchmarkData = e.detail;
    setupComponent();
  });
