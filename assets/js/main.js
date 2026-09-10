/* © 2026 Nopal Girl — Tutti i diritti riservati. Vietati uso, copia e distribuzione. Vedi LICENSE. */
/* ============================================================
   Nopal Girl — shared scripts (vanilla, no dependencies)
   ============================================================ */
(function () {
  'use strict';

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Navigation: scroll state, progress, mobile menu ---------- */
  const nav = $('.nav');
  const toggle = $('.mobile-toggle');
  const links = $('.nav-links');
  const progress = $('.progress');
  const toTop = $('.to-top');

  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      const y = window.scrollY;
      if (nav) nav.classList.toggle('scrolled', y > 40);
      if (progress) {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.transform = 'scaleX(' + (max > 0 ? y / max : 0) + ')';
      }
      if (toTop) toTop.classList.toggle('show', y > 600);
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  function closeMenu() {
    if (!links || !toggle) return;
    links.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      const open = links.classList.toggle('open');
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
      document.body.style.overflow = open ? 'hidden' : '';
    });
    $$('a', links).forEach(function (a) { a.addEventListener('click', closeMenu); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
  }
  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  }

  /* ---------- Reveal-on-scroll ---------- */
  const revealSel = '.reveal, .reveal-left, .reveal-scale';
  function observeReveal(root) {
    const els = $$(revealSel, root);
    if (!els.length) return;
    if (!('IntersectionObserver' in window) || reduceMotion) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }
  // Stagger: assegna --i ai figli dei contenitori [data-stagger]
  $$('[data-stagger]').forEach(function (wrap) {
    Array.from(wrap.children).forEach(function (child, i) { child.style.setProperty('--i', i); });
  });
  observeReveal(document);

  /* ---------- Sparkle dust ---------- */
  function buildSparkles(n) {
    if (reduceMotion) return;
    const host = document.createElement('div');
    host.className = 'sparkles';
    host.setAttribute('aria-hidden', 'true');
    const frag = document.createDocumentFragment();
    for (let i = 0; i < n; i++) {
      const s = document.createElement('span');
      s.className = 'sparkle';
      const size = Math.random() * 4 + 2;
      s.style.left = Math.random() * 100 + 'vw';
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      const dur = Math.random() * 10 + 12;
      s.style.animationDuration = dur + 's';
      s.style.animationDelay = Math.random() * -dur + 's';
      frag.appendChild(s);
    }
    host.appendChild(frag);
    document.body.appendChild(host);
  }
  buildSparkles(18);

  /* ---------- Link riservati (offuscati) ----------
     Gli URL sensibili (album Google Foto, contatto WhatsApp) sono salvati
     in forma codificata e scritti negli href solo a runtime: non compaiono
     mai in chiaro nel codice sorgente.
     Per cambiarli: codifica il nuovo URL in base64
       echo -n 'NUOVO-URL' | base64
     dividilo in 3 parti e sostituisci i pezzi qui sotto. */
  const SECRET_LINKS = {
    photos: ['aHR0cHM6Ly9waG90', 'b3MuYXBwLmdvby5nbC9qcFhTU3FNenFE', 'N0VHSHpzOQ=='],
    whatsapp: ['aHR0cHM6Ly93YS5t', 'ZS9xci8yN1BDRUVG', 'VlVYVkxLMQ==']
  };
  function decodeSecret(key) {
    try {
      const parts = SECRET_LINKS[key];
      if (!parts) return '#';
      return atob(parts.join(''));
    } catch (e) { return '#'; }
  }
  function revealSecrets() {
    $$('[data-secret]').forEach(function (a) {
      const url = decodeSecret(a.getAttribute('data-secret'));
      if (url && url.charAt(0) === 'h') a.setAttribute('href', url);
    });
  }

  /* ---------- Protezione contenuti ----------
     Deterrente anti-copia: blocca tasto destro, trascinamento dei media,
     copia/taglia, scorciatoie di salvataggio/ispezione e stampa.
     Nota onesta: nessuna protezione lato client è al 100%, ma scoraggia
     la copia occasionale. */
  const PROTECT_MSG = 'Contenuti protetti — riproduzione vietata';
  let toastEl = null;
  let toastTimer = null;
  function showToast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      toastEl.setAttribute('role', 'status');
      toastEl.setAttribute('aria-live', 'polite');
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2200);
  }

  // Tasto destro / long-press: disabilitati (tranne nei campi di testo)
  document.addEventListener('contextmenu', function (e) {
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    e.preventDefault();
    showToast(PROTECT_MSG);
  });

  // Trascinamento di immagini e video: disabilitato
  document.addEventListener('dragstart', function (e) { e.preventDefault(); });
  $$('img, video').forEach(function (m) {
    m.setAttribute('draggable', 'false');
    m.addEventListener('dragstart', function (e) { e.preventDefault(); });
  });

  // Copia e taglia: bloccati
  ['copy', 'cut'].forEach(function (evt) {
    document.addEventListener(evt, function (e) {
      e.preventDefault();
      showToast('Copia disabilitata — contenuti protetti');
    });
  });

  // Scorciatoie di ispezione/salvataggio/stampa: bloccate
  document.addEventListener('keydown', function (e) {
    const k = (e.key || '').toLowerCase();
    const mod = e.ctrlKey || e.metaKey;
    const blocked =
      e.key === 'F12' ||
      (e.ctrlKey && e.shiftKey && ['i', 'j', 'c', 'k'].indexOf(k) !== -1) ||
      (mod && !e.shiftKey && ['u', 's', 'p'].indexOf(k) !== -1);
    if (blocked) {
      e.preventDefault();
      showToast(PROTECT_MSG);
    }
  });

  // Tasto Stamp: best-effort, sporca gli appunti (se il browser lo permette)
  document.addEventListener('keyup', function (e) {
    if (e.key === 'PrintScreen') {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(PROTECT_MSG).catch(function () {});
        }
      } catch (err) { /* clipboard non disponibile: ignora */ }
      showToast(PROTECT_MSG);
    }
  });

  // Avviso in console per i curiosi
  try {
    console.log(
      '%cNopal Girl — Contenuti protetti da copyright. È vietata la riproduzione anche parziale.',
      'font-size:14px;font-weight:bold;color:#b97a3f;'
    );
  } catch (err) { /* console non disponibile: ignora */ }

  /* ---------- Hero video ---------- */
  function initVideo() {
    const video = $('.hero-video video');
    if (!video) return;
    const ready = function () { video.classList.add('is-ready'); };
    video.addEventListener('playing', ready, { once: true });
    const p = video.play();
    if (p && typeof p.catch === 'function') p.catch(function () { /* poster resta visibile */ });
    if (reduceMotion) { video.pause(); video.removeAttribute('autoplay'); }
  }

  /* ---------- Nav colore: chiaro sulle pagine senza hero scuro ---------- */
  if (nav && !$('.hero')) nav.classList.add('on-light');

  /* ---------- Footer year ---------- */
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  document.addEventListener('DOMContentLoaded', function () {
    initVideo();
    revealSecrets();
  });
})();
