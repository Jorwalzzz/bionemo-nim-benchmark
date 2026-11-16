/**
 * BioNeMo NIM Inference Benchmark - Campaign Scale Calculator
 * Module: ./js/calculator.js
 * 
 * Implements:
 * 1. Logarithmic scale slider (100 to 1,000,000 complexes).
 * 2. Quick scale chips (1k, 10k, 100k, 1M).
 * 3. Workload switcher (End-to-End Cycle, DiffDock, ESMFold, All 5 NIMs).
 * 4. Proportional mass blocks depicting physical wall-clock and energy collapsing.
 */

(function () {
  'use strict';

  let complexCount = 10000;
  let activeWorkload = 'cycle';

  // DOM elements cache
  let sliderEl = null;
  let countDisplayEl = null;
  let workloadSelectEl = null;
  let chipBtns = [];
  let kpiHoursSavedEl = null;
  let kpiHoursSubEl = null;
  let kpiSpeedupEl = null;
  let kpiKwhSavedEl = null;
  let kpiKwhSubEl = null;
  let massCpuFillEl = null;
  let massGpuFillEl = null;
  let massCpuLabelEl = null;
  let massGpuLabelEl = null;

  // Logarithmic slider helpers: 10^2 (100) to 10^6 (1,000,000)
  function sliderToCount(sliderVal) {
    const exponent = 2 + (sliderVal / 100) * 4;
    return Math.round(Math.pow(10, exponent));
  }

  function countToSlider(count) {
    const clamped = Math.max(100, Math.min(1000000, count));
    const exponent = Math.log10(clamped);
    return ((exponent - 2) / 4) * 100;
  }

  function formatNumber(num) {
    return num.toLocaleString('en-US');
  }

  function formatHoursOrDays(hours) {
    if (hours >= 48) {
      const days = (hours / 24).toFixed(1);
      return `${hours.toFixed(1)}h (${days} Days)`;
    }
    return `${hours.toFixed(1)}h`;
  }

  function updateCalculator() {
    if (!window.BioNeMoHydrator) return;
    const m = window.BioNeMoHydrator.calculateCampaign(complexCount, activeWorkload);

    // Update count display
    if (countDisplayEl) {
      countDisplayEl.textContent = `${formatNumber(m.complexCount)} Complexes`;
    }

    // Update KPIs
    if (kpiHoursSavedEl) {
      kpiHoursSavedEl.textContent = `${m.hoursSaved >= 100 ? Math.round(m.hoursSaved) : m.hoursSaved.toFixed(1)}h`;
    }
    if (kpiHoursSubEl) {
      const days = (m.hoursSaved / 24).toFixed(1);
      kpiHoursSubEl.textContent = m.hoursSaved >= 24 ? `${days} Days of Compute Time Saved` : `Direct wall-time saved`;
    }
    if (kpiSpeedupEl) {
      kpiSpeedupEl.textContent = `${m.speedupRatio}x`;
    }
    if (kpiKwhSavedEl) {
      kpiKwhSavedEl.textContent = `${m.kwhSaved >= 100 ? Math.round(m.kwhSaved) : m.kwhSaved.toFixed(1)} kWh`;
    }
    if (kpiKwhSubEl) {
      kpiKwhSubEl.textContent = `${m.energyReductionPct}% Estimated Power Reduction`;
    }

    // Update Proportional Mass Blocks
    if (massCpuFillEl) {
      massCpuFillEl.style.width = '100%';
    }
    if (massGpuFillEl) {
      const fillPct = Math.max(1.2, Math.min(100, (m.nimHours / (m.cpuHours || 1)) * 100));
      massGpuFillEl.style.width = `${fillPct.toFixed(1)}%`;
    }
    if (massCpuLabelEl) {
      massCpuLabelEl.textContent = `AMD EPYC 7763 (16 Cores): ${formatHoursOrDays(m.cpuHours)} (~${m.cpuKwh} kWh)`;
    }
    if (massGpuLabelEl) {
      massGpuLabelEl.textContent = `NVIDIA H100 SXM5: ${formatHoursOrDays(m.nimHours)} (~${m.nimKwh} kWh)`;
    }

    // Sync slider position if not active
    if (sliderEl && document.activeElement !== sliderEl) {
      sliderEl.value = countToSlider(complexCount);
    }

    // Sync quick chips
    chipBtns.forEach((chip) => {
      const val = parseInt(chip.getAttribute('data-count'), 10);
      if (val === complexCount) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });
  }

  function setComplexCount(count) {
    complexCount = Math.max(100, Math.min(1000000, count));
    updateCalculator();
  }

  function init() {
    sliderEl = document.getElementById('calc-slider');
    countDisplayEl = document.getElementById('calc-count-display');
    workloadSelectEl = document.getElementById('calc-workload-select');
    chipBtns = Array.from(document.querySelectorAll('.calc-chip-btn'));
    kpiHoursSavedEl = document.getElementById('calc-hours-saved');
    kpiHoursSubEl = document.getElementById('calc-hours-sub');
    kpiSpeedupEl = document.getElementById('calc-speedup');
    kpiKwhSavedEl = document.getElementById('calc-kwh-saved');
    kpiKwhSubEl = document.getElementById('calc-kwh-sub');
    massCpuFillEl = document.getElementById('mass-bar-cpu-fill');
    massGpuFillEl = document.getElementById('mass-bar-gpu-fill');
    massCpuLabelEl = document.getElementById('mass-cpu-label');
    massGpuLabelEl = document.getElementById('mass-gpu-label');

    // Slider listener
    if (sliderEl) {
      sliderEl.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        complexCount = sliderToCount(val);
        updateCalculator();
      });
    }

    // Quick chips
    chipBtns.forEach((chip) => {
      chip.addEventListener('click', () => {
        const count = parseInt(chip.getAttribute('data-count'), 10);
        setComplexCount(count);
      });
    });

    // Workload select
    if (workloadSelectEl) {
      workloadSelectEl.addEventListener('change', (e) => {
        activeWorkload = e.target.value;
        updateCalculator();
      });
    }

    // Initial update
    updateCalculator();
  }

  // DOM or Data Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.addEventListener('bionemo:data-ready', () => {
    updateCalculator();
  });
})();
