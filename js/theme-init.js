/**
 * Synchronous pre-paint theme initializer shared by index.html and cockpit.html.
 * Must load as a classic script in <head> with zero ES module imports to prevent FOUC.
 */
(function () {
  'use strict';
  var STORAGE_KEY = 'bionemo_theme';
  var root = document.documentElement;
  var saved = null;
  try {
    saved =
      localStorage.getItem(STORAGE_KEY) ||
      localStorage.getItem('bionemo-theme') ||
      localStorage.getItem('theme');
  } catch (_) {}

  var theme =
    saved === 'dark' || saved === 'light'
      ? saved
      : window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark';

  if (theme === 'light') {
    root.setAttribute('data-theme', 'light');
    root.classList.remove('dark');
    root.classList.add('light');
  } else {
    root.removeAttribute('data-theme');
    root.classList.remove('light');
    root.classList.add('dark');
  }
})();
