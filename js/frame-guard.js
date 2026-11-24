/**
 * CSP-compliant top-frame navigation guard, external CDN script fallback loader,
 * and declarative DOM trigger wiring shared by index.html and cockpit.html.
 */
(function () {
  'use strict';

  if (window.top !== window.self) {
    try {
      window.top.location = window.self.location;
    } catch (_) {
      document.documentElement.textContent = '';
    }
  }

  document.addEventListener(
    'error',
    function (event) {
      const target = event.target;
      if (target && target.tagName === 'SCRIPT') {
        const fallbackSrc = target.getAttribute('data-fallback-src');
        if (fallbackSrc && !target.dataset.fallbackAttempted) {
          target.dataset.fallbackAttempted = '1';
          const fallback = document.createElement('script');
          fallback.src = fallbackSrc;
          fallback.defer = target.defer;
          fallback.crossOrigin = 'anonymous';
          document.head.appendChild(fallback);
        }
      }
    },
    true
  );

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-action="copy-hero-terminal"]').forEach(function (el) {
      const copyHandler = function () {
        if (typeof window.copyHeroTerminal === 'function') {
          window.copyHeroTerminal(el);
        }
      };
      el.addEventListener('click', copyHandler);
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          copyHandler();
        }
      });
    });
  });
})();
