/* ============================================================
   PySPT Main Interactivity
   Language toggle, theme toggle, navigation, copy buttons
   ============================================================ */

(function () {
  'use strict';

  // ---- Language Toggle ----
  var langBtn = document.getElementById('lang-toggle');
  var htmlEl = document.documentElement;

  function detectLang() {
    var saved = localStorage.getItem('pyspt-lang');
    if (saved) return saved;
    return (navigator.language || '').startsWith('zh') ? 'zh' : 'en';
  }

  function setLang(lang) {
    htmlEl.setAttribute('lang', lang);
    langBtn.textContent = lang === 'zh' ? 'EN' : '中文';
    localStorage.setItem('pyspt-lang', lang);
  }

  setLang(detectLang());

  langBtn.addEventListener('click', function () {
    var current = htmlEl.getAttribute('lang');
    setLang(current === 'zh' ? 'en' : 'zh');
  });

  // ---- Theme Toggle ----
  var themeBtn = document.getElementById('theme-toggle');

  function detectTheme() {
    var saved = localStorage.getItem('pyspt-theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme) {
    htmlEl.setAttribute('data-theme', theme);
    // Moon for light (click to go dark), Sun for dark (click to go light)
    themeBtn.innerHTML = theme === 'light' ? '&#9790;' : '&#9728;';
    localStorage.setItem('pyspt-theme', theme);
  }

  setTheme(detectTheme());

  themeBtn.addEventListener('click', function () {
    var current = htmlEl.getAttribute('data-theme');
    setTheme(current === 'light' ? 'dark' : 'light');
  });

  // ---- Navbar scroll effect ----
  var navbar = document.getElementById('navbar');

  function onScroll() {
    if (window.scrollY > 20) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---- Hamburger menu ----
  var hamburger = document.getElementById('hamburger');
  var navLinks = document.getElementById('nav-links');

  hamburger.addEventListener('click', function () {
    navLinks.classList.toggle('open');
  });

  // Close menu on link click
  navLinks.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') {
      navLinks.classList.remove('open');
    }
  });

  // ---- Code copy buttons ----
  window.copyCode = function (btn) {
    var pre = btn.closest('.code-block').querySelector('pre');
    if (!pre) return;
    var text = pre.textContent;
    navigator.clipboard.writeText(text).then(function () {
      btn.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(function () {
        btn.textContent = 'Copy';
        btn.classList.remove('copied');
      }, 2000);
    });
  };

  // ---- Install button copy ----
  window.copyInstall = function (btn) {
    navigator.clipboard.writeText('pip install pyspt').then(function () {
      var hint = btn.querySelector('.copy-hint');
      if (hint) {
        var origZh = hint.getAttribute('data-lang') === 'zh';
        hint.textContent = 'Copied!';
        setTimeout(function () {
          hint.textContent = origZh ? '点击复制' : 'click to copy';
        }, 2000);
      }
    });
  };

  // ---- Parity badges (loaded from docs/data/api.json) ----
  // For every <span class="func-tag">fn</span>, look up *fn* in the
  // parity registry and append a "✓ <ref>" badge if verified. Runs
  // once after DOMContentLoaded; silently no-ops if api.json is
  // missing (e.g. local preview before `python scripts/export_api.py`).
  //
  // Scope of "verified" (deliberately conservative):
  //   The badge means *this function's declared fixture cases*
  //   match the reference implementation to within the per-case
  //   tolerance recorded in the .npz metadata. It does NOT mean
  //   every parameter combination, shape, dtype, or edge case
  //   has been exercised. The reference label and fixture count
  //   are read from api.json so they stay in sync with the live
  //   registry (no hardcoded "R2025b" string here).
  function shortRefLabel(reference) {
    // "MATLAB R2025b Signal Processing Toolbox — chirp" → "MATLAB R2025b"
    // Falls back to the full string if it doesn't start with a
    // recognizable "TOOL <version>" prefix.
    var m = reference.match(/^(\S+\s+[A-Za-z0-9.]+)/);
    return m ? m[1] : reference;
  }

  function annotateVerifiedFuncs() {
    var url = 'data/api.json';
    fetch(url, { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.functions) return;
        // Map "name" -> entry so we can show the full reference and
        // the declared-fixture count (NOT all possible inputs).
        var verified = {};
        Object.keys(data.functions).forEach(function (k) {
          var entry = data.functions[k];
          verified[entry.name] = entry;
        });

        var tags = document.querySelectorAll('.module-funcs .func-tag');
        tags.forEach(function (tag) {
          var fname = tag.textContent.trim();
          var entry = verified[fname];
          if (!entry) return;
          var label = shortRefLabel(entry.reference);
          var sup = document.createElement('sup');
          sup.className = 'func-tag-verified';
          sup.title =
            'Parity claim: ' + entry.reference + '\n' +
            'Coverage: ' + entry.fixtures.length +
            ' declared fixture case(s).\n' +
            'Scope: only the declared cases (and inputs) above are ' +
            'compared to the reference within each fixture\'s tolerance. ' +
            'Other parameters, shapes, and edge conditions are not ' +
            'automatically covered by this badge.';
          sup.textContent = '\u2713 ' + label;
          tag.appendChild(sup);
        });
      })
      .catch(function () { /* offline preview: skip silently */ });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', annotateVerifiedFuncs);
  } else {
    annotateVerifiedFuncs();
  }

})();
