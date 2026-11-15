/**
 * BioNeMo NIM Inference Benchmark - "Time Collapsing" Race Controller
 * Module: ./js/race-scroll.js
 * 
 * Implements:
 * - Scroll-scrubbed & slider-scrubbed physical race simulation.
 * - Dynamic workload switcher (DiffDock, ESMFold, ESM-2, MolMIM, OpenFold).
 * - Instantaneous GPU flash visualization at exact latency ratio (e.g. 1.68% for DiffDock).
 * - "Replay Flash" simulated playback.
 */

(function () {
  'use strict';

  // Workload telemetry profiles (ground-truth parity)
  const WORKLOADS = {
    diffdock: {
      id: "bench_03",
      name: "DiffDock // BCR-ABL1 (2HYY)",
      shortName: "DiffDock 2HYY",
      cpu: 68.40,
      gpu: 1.15,
      speedup: 59.5,
      spec: "275 aa receptor + 42-atom ligand (Imatinib)"
    },
    esmfold: {
      id: "bench_02",
      name: "ESMFold // DHFR (1DHF)",
      shortName: "ESMFold 1DHF",
      cpu: 42.10,
      gpu: 0.72,
      speedup: 58.5,
      spec: "186 aa sequence"
    },
    esm2: {
      id: "bench_01",
      name: "ESM-2 (650M) // Ubiquitin (1UBQ)",
      shortName: "ESM-2 1UBQ",
      cpu: 3.20,
      gpu: 0.08,
      speedup: 40.0,
      spec: "76 aa sequence"
    },
    molmim: {
      id: "bench_04",
      name: "MolMIM 70M // EGFR (1M17)",
      shortName: "MolMIM 1M17",
      cpu: 14.80,
      gpu: 0.28,
      speedup: 52.9,
      spec: "31 heavy atoms seed analogue"
    },
    openfold: {
      id: "bench_05",
      name: "OpenFold // RdRp (7BV2)",
      shortName: "OpenFold 7BV2",
      cpu: 185.00,
      gpu: 2.94,
      speedup: 62.9,
      spec: "932 aa macromolecular complex"
    }
  };

  let currentKey = 'diffdock';
  let progress = 1.0; // Default to full race completion so visitor immediately sees the collapsed state
  let isSimulating = false;
  let simAnimId = null;

  // DOM elements cache
  let scrubInput = null;
  let barCpu = null;
  let barGpu = null;
  let timerCpu = null;
  let timerGpu = null;
  let tagCpu = null;
  let tagGpu = null;
  let speedupEl = null;
  let markerEnd = null;
  let replayBtn = null;
  let pillBtns = [];

  function updateRaceVisuals() {
    const workload = WORKLOADS[currentKey] || WORKLOADS.diffdock;
    const cpuTotal = workload.cpu;
    const gpuTotal = workload.gpu;
    const gpuFinishRatio = gpuTotal / cpuTotal;

    // CPU Bar & Timer
    const cpuPct = Math.min(100, Math.max(0, progress * 100));
    const cpuCurrentSec = progress * cpuTotal;
    if (barCpu) barCpu.style.width = `${cpuPct.toFixed(1)}%`;
    if (timerCpu) timerCpu.textContent = `${cpuCurrentSec.toFixed(2)}s / ${cpuTotal.toFixed(2)}s`;
    if (tagCpu) {
      if (progress >= 0.999) {
        tagCpu.classList.add('active');
        tagCpu.textContent = `FINISHED ${cpuTotal.toFixed(2)}s`;
      } else {
        tagCpu.classList.remove('active');
      }
    }

    // GPU Bar & Timer
    if (progress >= gpuFinishRatio) {
      if (barGpu) barGpu.style.width = '100%';
      if (timerGpu) timerGpu.textContent = `${gpuTotal.toFixed(2)}s / ${gpuTotal.toFixed(2)}s`;
      if (tagGpu) {
        tagGpu.classList.add('active');
        tagGpu.textContent = `FLASH ${gpuTotal.toFixed(2)}s (${workload.speedup}x)`;
      }
    } else {
      const gpuPct = (progress / gpuFinishRatio) * 100;
      const gpuCurrentSec = progress * cpuTotal;
      if (barGpu) barGpu.style.width = `${Math.min(100, gpuPct).toFixed(1)}%`;
      if (timerGpu) timerGpu.textContent = `${gpuCurrentSec.toFixed(2)}s / ${gpuTotal.toFixed(2)}s`;
      if (tagGpu) tagGpu.classList.remove('active');
    }

    // Scrub slider sync
    if (scrubInput && !isSimulating) {
      scrubInput.value = Math.round(progress * 100);
    }
  }

  function setWorkload(key) {
    if (!WORKLOADS[key]) return;
    currentKey = key;
    const workload = WORKLOADS[key];

    // Update pill states
    pillBtns.forEach((btn) => {
      const btnKey = btn.getAttribute('data-workload');
      if (btnKey === key) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update markers and speedup label
    if (speedupEl) {
      speedupEl.textContent = `${workload.speedup}x FASTER`;
    }
    if (markerEnd) {
      markerEnd.textContent = `${workload.cpu.toFixed(1)}s (100%)`;
    }

    updateRaceVisuals();
  }

  function startReplay() {
    if (isSimulating) {
      cancelAnimationFrame(simAnimId);
    }
    isSimulating = true;
    progress = 0;
    updateRaceVisuals();

    const simulationDurationMs = 2800; // Complete visual simulation cycle in 2.8s
    const startTime = performance.now();

    function step(now) {
      const elapsed = now - startTime;
      const rawProgress = Math.min(1, elapsed / simulationDurationMs);

      // Smooth ease-out cubic for realistic deceleration
      progress = rawProgress;
      updateRaceVisuals();

      if (rawProgress < 1) {
        simAnimId = requestAnimationFrame(step);
      } else {
        isSimulating = false;
        progress = 1.0;
        updateRaceVisuals();
      }
    }

    simAnimId = requestAnimationFrame(step);
  }

  function initScrollObserver() {
    const raceSection = document.getElementById('race');
    if (!raceSection) return;

    let hasScrolledTriggered = false;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasScrolledTriggered) {
            hasScrolledTriggered = true;
            // Trigger automatic replay flash on first scroll into view
            setTimeout(() => {
              startReplay();
            }, 300);
          }
        });
      },
      { threshold: 0.35 }
    );

    observer.observe(raceSection);
  }

  function init() {
    scrubInput = document.getElementById('race-scrub-input');
    barCpu = document.getElementById('bar-cpu');
    barGpu = document.getElementById('bar-gpu');
    timerCpu = document.getElementById('timer-cpu');
    timerGpu = document.getElementById('timer-gpu');
    tagCpu = document.getElementById('tag-cpu');
    tagGpu = document.getElementById('tag-gpu');
    speedupEl = document.getElementById('race-speedup-multiplier');
    markerEnd = document.getElementById('race-marker-end');
    replayBtn = document.getElementById('btn-replay-flash');
    pillBtns = Array.from(document.querySelectorAll('#race-pills .workload-pill-btn'));

    // Workload pill events
    pillBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.getAttribute('data-workload');
        setWorkload(key);
        startReplay();
      });
    });

    // Manual slider scrub
    if (scrubInput) {
      scrubInput.addEventListener('input', (e) => {
        if (isSimulating) {
          cancelAnimationFrame(simAnimId);
          isSimulating = false;
        }
        progress = parseFloat(e.target.value) / 100;
        updateRaceVisuals();
      });
    }

    // Replay button
    if (replayBtn) {
      replayBtn.addEventListener('click', () => {
        startReplay();
      });
    }

    // Set initial workload
    setWorkload('diffdock');

    // Init scroll trigger
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion) {
      initScrollObserver();
    }
  }

  // Bind to DOM ready or data ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.addEventListener('bionemo:data-ready', () => {
    // If dynamic data had custom items, refresh
    updateRaceVisuals();
  });
})();
