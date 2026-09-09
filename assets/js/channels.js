/* ------------------------------------------------------------------
   Hero channel viewer.

   Builds a synthetic sample — dense inclusions plus oriented fibre
   bundles — and renders it four ways: transmission, propagation phase
   contrast, dark-field, and directional dark-field.

   To swap in a real dataset, replace buildFields() with a loader for
   four pre-computed 8-bit PNGs and drop the maths entirely; the tab
   and crossfade logic below does not care where the pixels came from.
------------------------------------------------------------------- */
(function () {
  var cv = document.getElementById('chan');
  if (!cv || !cv.getContext) return;
  var ctx = cv.getContext('2d');
  var N = cv.width;

  var bundles = [
    { x: .30, y: .33, rx: .22,  ry: .125, a: -0.42, f: 1.15, amp: .95 },
    { x: .66, y: .58, rx: .175, ry: .105, a:  1.18, f: 1.45, amp: .85 },
    { x: .38, y: .74, rx: .20,  ry: .085, a:  0.22, f: 1.05, amp: .75 }
  ];
  var discs = [
    { x: .70, y: .27, r: .115 },
    { x: .24, y: .63, r: .078 },
    { x: .80, y: .80, r: .062 }
  ];

  var att = new Float32Array(N * N),
      fib = new Float32Array(N * N),
      ox  = new Float32Array(N * N),
      oy  = new Float32Array(N * N);

  (function buildFields() {
    for (var y = 0; y < N; y++) {
      for (var x = 0; x < N; x++) {
        var i = y * N + x, u = x / N, v = y / N;
        var a = 0.16, f = 0, sx = 0, sy = 0, k, b, d;

        for (k = 0; k < discs.length; k++) {
          d = discs[k];
          var ddx = u - d.x, ddy = v - d.y;
          var rr = d.r * d.r - ddx * ddx - ddy * ddy;
          if (rr > 0) a += Math.sqrt(rr) / d.r * 0.95;
        }

        for (k = 0; k < bundles.length; k++) {
          b = bundles[k];
          var dx = u - b.x, dy = v - b.y;
          var ca = Math.cos(b.a), sa = Math.sin(b.a);
          var pu = dx * ca + dy * sa, pv = -dx * sa + dy * ca;
          var e = 1 - (pu * pu) / (b.rx * b.rx) - (pv * pv) / (b.ry * b.ry);
          if (e > 0) {
            var w = Math.min(1, e * 2.4);
            var stri = 0.5 + 0.5 * Math.sin(pv * N * b.f * 0.42);
            var g = w * (0.35 + 0.65 * stri) * b.amp;
            f += g;
            a += g * 0.13;
            sx += g * Math.cos(2 * b.a);   /* doubled-angle averaging: */
            sy += g * Math.sin(2 * b.a);   /* orientation is mod pi     */
          }
        }
        att[i] = a; fib[i] = f; ox[i] = sx; oy[i] = sy;
      }
    }
  })();

  function clamp(v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }
  function make(fn) {
    var im = ctx.createImageData(N, N), p = im.data;
    for (var y = 0; y < N; y++) for (var x = 0; x < N; x++) fn(y * N + x, x, y, p, (y * N + x) * 4);
    return im;
  }

  /* 1 — transmission: Beer–Lambert through a warm grey ramp */
  var imT = make(function (i, x, y, p, o) {
    var t = Math.exp(-att[i] * 1.55);
    p[o] = clamp(30 + t * 216); p[o + 1] = clamp(26 + t * 206); p[o + 2] = clamp(22 + t * 190); p[o + 3] = 255;
  });

  /* 2 — phase: Laplacian edge enhancement around a mid grey */
  var imP = make(function (i, x, y, p, o) {
    var xm = x > 0 ? i - 1 : i, xp = x < N - 1 ? i + 1 : i;
    var ym = y > 0 ? i - N : i, yp = y < N - 1 ? i + N : i;
    var lap = 4 * att[i] - att[xm] - att[xp] - att[ym] - att[yp];
    var g = 0.52 + lap * 7.5; g = g < 0 ? 0 : (g > 1 ? 1 : g);
    p[o] = clamp(24 + g * 222); p[o + 1] = clamp(22 + g * 214); p[o + 2] = clamp(20 + g * 200); p[o + 3] = 255;
  });

  /* 3 — dark-field: scattering power only, amber ramp */
  var imD = make(function (i, x, y, p, o) {
    var s = fib[i]; s = s > 1 ? 1 : s; s = Math.pow(s, 0.75);
    p[o] = clamp(14 + s * 236); p[o + 1] = clamp(11 + s * 168); p[o + 2] = clamp(8 + s * 66); p[o + 3] = 255;
  });

  /* 4 — directional: hue = orientation, value = scattering power */
  var imO = make(function (i, x, y, p, o) {
    var s = fib[i]; s = s > 1 ? 1 : s; s = Math.pow(s, 0.72);
    if (s < 0.02) { p[o] = 14; p[o + 1] = 11; p[o + 2] = 8; p[o + 3] = 255; return; }
    var ang = Math.atan2(oy[i], ox[i]) / 2;
    var h = ((ang / Math.PI) + 1) % 1;
    var q = h * 6, c = Math.floor(q), fp = q - c, sat = 0.72;
    var vmax = s, vmin = vmax * (1 - sat), v1 = vmax * (1 - sat * fp), v2 = vmax * (1 - sat * (1 - fp));
    var r, g, bl;
    switch (c % 6) {
      case 0: r = vmax; g = v2;   bl = vmin; break;
      case 1: r = v1;   g = vmax; bl = vmin; break;
      case 2: r = vmin; g = vmax; bl = v2;   break;
      case 3: r = vmin; g = v1;   bl = vmax; break;
      case 4: r = v2;   g = vmin; bl = vmax; break;
      default: r = vmax; g = vmin; bl = v1;
    }
    p[o] = clamp(12 + r * 243); p[o + 1] = clamp(10 + g * 243); p[o + 2] = clamp(8 + bl * 243); p[o + 3] = 255;
  });

  var frames = [imT, imP, imD, imO];
  var cap = document.getElementById('cap');
  var caps = cap ? JSON.parse(cap.getAttribute('data-captions')) : [];
  var tabs = [0, 1, 2, 3].map(function (k) { return document.getElementById('tab' + k); });
  if (tabs.some(function (t) { return !t; })) return;

  var cur = 0, raf = null;
  var off = document.createElement('canvas'); off.width = off.height = N;
  var octx = off.getContext('2d');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function show(k) {
    if (k === cur) return;
    tabs[cur].setAttribute('aria-selected', 'false');
    tabs[k].setAttribute('aria-selected', 'true');
    if (cap && caps[k]) cap.innerHTML = caps[k];
    if (reduce) { cur = k; ctx.putImageData(frames[k], 0, 0); return; }
    octx.putImageData(frames[cur], 0, 0);
    var from = off, t0 = performance.now();
    cur = k;
    if (raf) cancelAnimationFrame(raf);
    (function step(now) {
      var e = Math.min(1, (now - t0) / 260);
      ctx.putImageData(frames[cur], 0, 0);
      if (e < 1) {
        ctx.save(); ctx.globalAlpha = 1 - e; ctx.drawImage(from, 0, 0); ctx.restore();
        raf = requestAnimationFrame(step);
      } else { raf = null; }
    })(t0);
  }

  tabs.forEach(function (btn, k) {
    btn.addEventListener('click', function () { show(k); });
    btn.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') {
        ev.preventDefault();
        var n = (k + (ev.key === 'ArrowRight' ? 1 : 3)) % 4;
        tabs[n].focus(); show(n);
      }
    });
  });

  ctx.putImageData(frames[0], 0, 0);
})();
