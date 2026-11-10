// Slide viewer for course decks: one <figure class="frame"> per slide or click step.
(function () {
  const deck = document.getElementById('deck');
  if (!deck) return;
  const frames = Array.from(deck.querySelectorAll('.frame'));
  const cur = document.getElementById('cur');
  let i = 0;

  // frame index of the last step of slide n (the slide as it finally looks)
  const lastOf = n => { let k = -1; frames.forEach((f, j) => { if (+f.dataset.n === n) k = j; }); return k; };
  const firstOf = n => frames.findIndex(f => +f.dataset.n === n);

  function warm(j) {           // start loading the neighbours so advancing is instant
    [j + 1, j + 2, j - 1].forEach(k => {
      const img = frames[k] && frames[k].querySelector('img');
      if (img) img.loading = 'eager';
    });
  }

  function show(j, fromHash) {
    j = Math.max(0, Math.min(frames.length - 1, j));
    frames[i].hidden = true;
    frames[i].querySelectorAll('video').forEach(v => v.pause());
    i = j;
    const f = frames[i];
    f.hidden = false;
    f.querySelector('img').loading = 'eager';
    f.querySelectorAll('video').forEach(v => { v.preload = 'auto'; const p = v.play(); if (p) p.catch(() => {}); });
    cur.textContent = f.dataset.n;
    warm(i);
    if (!fromHash) history.replaceState(null, '', '#' + f.dataset.n);
  }

  const next = () => show(i + 1);
  const prev = () => show(i - 1);

  deck.querySelector('.zone.next').addEventListener('click', next);
  deck.querySelector('.zone.prev').addEventListener('click', prev);
  document.querySelectorAll('.deckbar .db').forEach(b => b.addEventListener('click', () => {
    const a = b.dataset.act;
    if (a === 'next') next();
    else if (a === 'prev') prev();
    else if (a === 'first') show(0);
    else if (a === 'last') show(frames.length - 1);
    else if (a === 'full') toggleFull();
  }));

  function toggleFull() {
    if (document.fullscreenElement) document.exitFullscreen();
    else if (deck.requestFullscreen) deck.requestFullscreen().then(() => deck.focus()).catch(() => {});
  }

  document.addEventListener('keydown', e => {
    if (e.target.closest('input, textarea')) return;
    const k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || (k === ' ' && document.activeElement === deck)) { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); prev(); }
    else if (k === 'Home') { e.preventDefault(); show(0); }
    else if (k === 'End') { e.preventDefault(); show(frames.length - 1); }
    else if (k === 'f' || k === 'F') toggleFull();
  });

  let x0 = null;
  deck.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  deck.addEventListener('touchend', e => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) (dx < 0 ? next : prev)();
    x0 = null;
  });

  document.querySelectorAll('.thumbs a[data-go]').forEach(a => a.addEventListener('click', e => {
    e.preventDefault();
    show(firstOf(+a.dataset.go));
    deck.scrollIntoView({ behavior: 'smooth', block: 'center' });
    deck.focus({ preventScroll: true });
  }));

  function fromHash() {
    const n = parseInt(location.hash.slice(1), 10);
    if (n) { const j = lastOf(n) >= 0 ? firstOf(n) : 0; show(j, true); }
  }
  window.addEventListener('hashchange', fromHash);
  // no element full screen on iPhone Safari: hide the button rather than offer nothing
  if (!deck.requestFullscreen) document.querySelectorAll('[data-act="full"]').forEach(b => b.hidden = true);
  frames[0].hidden = false;
  show(0, true);
  fromHash();
})();
