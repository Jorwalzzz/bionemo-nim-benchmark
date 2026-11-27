/**
 * NVIDIA BioNeMo & NIM Inference Benchmark — Theme Toggle, Progress Hairline & Lab Cursor
 * Pre-paint theme class/attribute initialization lives synchronously in ./js/theme-init.js.
 */

(function () {
  'use strict';

  var STORAGE_KEY = 'bionemo_theme';
  var htmlEl = document.documentElement;

  function getPreferredTheme() {
    var saved = null;
    try {
      saved =
        localStorage.getItem(STORAGE_KEY) ||
        localStorage.getItem('bionemo-theme') ||
        localStorage.getItem('theme');
    } catch (_) {}
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
      ? 'light'
      : 'dark';
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      htmlEl.setAttribute('data-theme', 'light');
      htmlEl.classList.remove('dark');
      htmlEl.classList.add('light');
      if (document.body) {
        document.body.setAttribute('data-theme', 'light');
        document.body.classList.remove('dark');
        document.body.classList.add('light');
      }
    } else {
      htmlEl.removeAttribute('data-theme');
      htmlEl.classList.remove('light');
      htmlEl.classList.add('dark');
      if (document.body) {
        document.body.removeAttribute('data-theme');
        document.body.classList.remove('light');
        document.body.classList.add('dark');
      }
    }
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {}
    updateThemeIcon(theme);
    try {
      window.dispatchEvent(new CustomEvent('bionemo:theme-changed', { detail: { theme: theme } }));
    } catch (_) {}
  }

  function updateThemeIcon(theme) {
    var iconContainer = document.getElementById('themeToggleIcon');
    if (!iconContainer) return;
    if (theme === 'light') {
      iconContainer.innerHTML =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>';
    } else {
      iconContainer.innerHTML =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>';
    }
  }

  function initThemeModule() {
    var current = htmlEl.getAttribute('data-theme') === 'light' ? 'light' : getPreferredTheme();
    applyTheme(current);

    var toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn && !toggleBtn.dataset.themeBound) {
      toggleBtn.dataset.themeBound = 'true';
      toggleBtn.addEventListener('click', function () {
        var now = htmlEl.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
        applyTheme(now === 'dark' ? 'light' : 'dark');
      });
    }

    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: light)');
      var onChange = function (e) {
        try {
          if (!localStorage.getItem(STORAGE_KEY)) {
            applyTheme(e.matches ? 'light' : 'dark');
          }
        } catch (_) {}
      };
      if (typeof mq.addEventListener === 'function') {
        mq.addEventListener('change', onChange);
      }
    }

    var progressBar = document.getElementById('navProgressBar');
    if (progressBar) {
      var scrollTicking = false;
      var syncScrollProgress = function () {
        scrollTicking = false;
        var winScroll = document.documentElement.scrollTop || document.body.scrollTop;
        var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        var ratio = height > 0 ? winScroll / height : 0;
        var clamped = Math.min(1, Math.max(0, ratio));
        progressBar.style.transform = 'scaleX(' + clamped.toFixed(4) + ')';
      };
      window.addEventListener(
        'scroll',
        function () {
          if (!scrollTicking) {
            scrollTicking = true;
            window.requestAnimationFrame(syncScrollProgress);
          }
        },
        { passive: true }
      );
      syncScrollProgress();
    }

    // Native OS cursor enforced across all pages; custom dual-cursor RAF loop removed.
    window.copyHeroTerminal = function (btn) {
      var text = 'git clone https://github.com/Jorwalzzz/bionemo-nim-benchmark.git';
      var onCopied = function () {
        var originalNodes = Array.prototype.slice.call(btn.childNodes);
        var feedback = document.createElement('span');
        feedback.className = 'hero-terminal-cmd';
        feedback.style.color = 'var(--color-signal-green)';
        feedback.style.fontWeight = '700';
        feedback.textContent = 'Copied git clone command';
        btn.replaceChildren(feedback);
        setTimeout(function () {
          btn.replaceChildren.apply(btn, originalNodes);
        }, 2200);
      };
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        navigator.clipboard.writeText(text).then(onCopied).catch(function () {});
      }
    };

    document.querySelectorAll('[data-action="copy-hero-terminal"]').forEach(function (el) {
      if (el.dataset.copyBound) return;
      el.dataset.copyBound = '1';
      el.addEventListener('click', function () {
        window.copyHeroTerminal(el);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeModule);
  } else {
    initThemeModule();
  }
})();
