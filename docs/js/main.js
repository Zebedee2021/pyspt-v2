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

})();
