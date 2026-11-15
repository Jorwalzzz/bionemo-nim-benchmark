/**
 * NVIDIA BioNeMo & NIM Inference Benchmark — Theme & Micro-Interactions Engine (v4.0.0)
 * Supports Dark & Warm Paper Light themes, OS sync, scroll progress, and custom cursor ring.
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'bionemo_theme';
  const htmlEl = document.documentElement;

  // ---------------------------------------------------------------------------
  // 1. THEME INITIALIZATION & TOGGLE
  // ---------------------------------------------------------------------------
  function getPreferredTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      htmlEl.setAttribute('data-theme', 'light');
    } else {
      htmlEl.removeAttribute('data-theme');
    }
    localStorage.setItem(STORAGE_KEY, theme);
    updateThemeIcon(theme);
  }

  function updateThemeIcon(theme) {
    const iconContainer = document.getElementById('themeToggleIcon');
    if (!iconContainer) return;
    if (theme === 'light') {
      // Moon icon (switch to dark)
      iconContainer.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>`;
    } else {
      // Sun icon (switch to light)
      iconContainer.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>`;
    }
  }

  // Apply immediately before DOM render to prevent theme flashing
  const initialTheme = getPreferredTheme();
  applyTheme(initialTheme);

  document.addEventListener('DOMContentLoaded', () => {
    updateThemeIcon(getPreferredTheme());

    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const current = htmlEl.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
      });
    }

    // Listen to OS scheme changes if user hasn't explicitly set preference
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
          applyTheme(e.matches ? 'light' : 'dark');
        }
      });
    }

    // -------------------------------------------------------------------------
    // 2. SCROLL PROGRESS HAIRLINE INDICATOR
    // -------------------------------------------------------------------------
    const progressBar = document.getElementById('navProgressBar');
    if (progressBar) {
      window.addEventListener('scroll', () => {
        const winScroll = document.documentElement.scrollTop || document.body.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
        progressBar.style.width = Math.min(100, Math.max(0, scrolled)) + '%';
      }, { passive: true });
    }

    // -------------------------------------------------------------------------
    // 3. DESKTOP CUSTOM CURSOR RING
    // -------------------------------------------------------------------------
    const hasFinePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (hasFinePointer && !reducedMotion) {
      const ring = document.createElement('div');
      ring.className = 'cursor-ring';
      const dot = document.createElement('div');
      dot.className = 'cursor-dot';
      document.body.appendChild(ring);
      document.body.appendChild(dot);

      let mouseX = -100;
      let mouseY = -100;
      let ringX = -100;
      let ringY = -100;

      window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        dot.style.left = mouseX + 'px';
        dot.style.top = mouseY + 'px';
      }, { passive: true });

      function renderCursor() {
        ringX += (mouseX - ringX) * 0.22;
        ringY += (mouseY - ringY) * 0.22;
        ring.style.left = ringX + 'px';
        ring.style.top = ringY + 'px';
        requestAnimationFrame(renderCursor);
      }
      requestAnimationFrame(renderCursor);

      // Magnetic hover enlargement
      const interactiveTargets = 'a, button, input, select, textarea, .hero-terminal-pill, [role="button"]';
      document.addEventListener('mouseover', (e) => {
        if (e.target.closest(interactiveTargets)) {
          ring.classList.add('cursor-hover');
        }
      });
      document.addEventListener('mouseout', (e) => {
        if (e.target.closest(interactiveTargets)) {
          ring.classList.remove('cursor-hover');
        }
      });
    }

    // -------------------------------------------------------------------------
    // 4. ONE-CLICK CLIPBOARD COPY FOR TERMINAL PILL
    // -------------------------------------------------------------------------
    window.copyHeroTerminal = function (btn) {
      const text = 'git clone https://github.com/Jorwalzzz/bionemo-nim-benchmark.git';
      if (!navigator.clipboard) return;
      navigator.clipboard.writeText(text).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<span class="hero-terminal-cmd" style="color:var(--color-signal-green);font-weight:700;">✓ Copied to clipboard</span>`;
        setTimeout(() => {
          btn.innerHTML = originalHtml;
        }, 2200);
      }).catch(err => {
        console.warn('Clipboard write error:', err);
      });
    };
  });
})();
