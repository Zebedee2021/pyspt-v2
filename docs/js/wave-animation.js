/* ============================================================
   PySPT Hero Wave Animation (Canvas)
   Draws layered sine waves with chirp-like frequency variation
   ============================================================ */

(function () {
  'use strict';

  var canvas = document.getElementById('hero-canvas');
  if (!canvas) return;

  var ctx = canvas.getContext('2d');
  var animId = null;
  var time = 0;
  var paused = false;

  // Check reduced motion preference
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function resize() {
    var dpr = window.devicePixelRatio || 1;
    var rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // Wave configuration
  var waves = [
    { amplitude: 0.12, frequency: 1.2, speed: 0.015, phase: 0, yOffset: 0.55 },
    { amplitude: 0.08, frequency: 2.0, speed: 0.020, phase: 2.0, yOffset: 0.50 },
    { amplitude: 0.06, frequency: 3.2, speed: 0.012, phase: 4.0, yOffset: 0.60 },
    { amplitude: 0.04, frequency: 4.5, speed: 0.025, phase: 1.0, yOffset: 0.45 }
  ];

  function getColors() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      return [
        'rgba(96, 165, 250, 0.12)',
        'rgba(139, 92, 246, 0.08)',
        'rgba(52, 211, 153, 0.06)',
        'rgba(96, 165, 250, 0.05)'
      ];
    }
    return [
      'rgba(59, 130, 246, 0.13)',
      'rgba(139, 92, 246, 0.09)',
      'rgba(16, 185, 129, 0.07)',
      'rgba(59, 130, 246, 0.05)'
    ];
  }

  function drawWave(w, color, width, height) {
    ctx.beginPath();
    var y0 = height * w.yOffset;
    ctx.moveTo(0, y0);

    for (var x = 0; x <= width; x += 2) {
      var nx = x / width;
      // Chirp-like effect: frequency increases along x
      var freq = w.frequency * (1 + nx * 0.5);
      var y = y0 + Math.sin(nx * freq * Math.PI * 2 + w.phase + time * w.speed * 60) * height * w.amplitude;
      ctx.lineTo(x, y);
    }

    // Fill to bottom
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  function draw() {
    var rect = canvas.parentElement.getBoundingClientRect();
    var width = rect.width;
    var height = rect.height;

    ctx.clearRect(0, 0, width, height);

    var colors = getColors();
    for (var i = 0; i < waves.length; i++) {
      drawWave(waves[i], colors[i], width, height);
    }

    time += 1;
  }

  function loop() {
    if (!paused) {
      draw();
    }
    animId = requestAnimationFrame(loop);
  }

  // Pause when tab not visible
  document.addEventListener('visibilitychange', function () {
    paused = document.hidden;
  });

  // Respond to theme changes
  var observer = new MutationObserver(function () {
    if (!paused) draw();
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  // Init
  resize();
  window.addEventListener('resize', resize);

  if (prefersReducedMotion) {
    // Draw once, static
    draw();
  } else {
    loop();
  }
})();
