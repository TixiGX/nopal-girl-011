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

  /* ---------- Gallery renderer + lightbox ----------
     Le foto arrivano da assets/data/photos.json, generato dallo script
     di sync che legge l'album condiviso di Google Foto. */
  function escapeHtml(s) {
    return String(s).replace(/[&<>\"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  let lbItems = [];
  let lbIndex = 0;
  let lightbox = null;

  function buildLightbox() {
    lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.setAttribute('role', 'dialog');
    lightbox.setAttribute('aria-modal', 'true');
    lightbox.setAttribute('aria-label', 'Immagine ingrandita');
    lightbox.innerHTML =
      '<button class="lb-btn lb-close" aria-label="Chiudi"><i class="fas fa-xmark"></i></button>' +
      '<button class="lb-btn lb-prev" aria-label="Precedente"><i class="fas fa-chevron-left"></i></button>' +
      '<button class="lb-btn lb-next" aria-label="Successiva"><i class="fas fa-chevron-right"></i></button>' +
      '<figure><img alt="" referrerpolicy="no-referrer"><figcaption><h3></h3><p></p></figcaption></figure>' +
      '<div class="lb-counter"></div>';
    document.body.appendChild(lightbox);

    $('.lb-close', lightbox).addEventListener('click', closeLightbox);
    $('.lb-prev', lightbox).addEventListener('click', function () { showLightbox(lbIndex - 1); });
    $('.lb-next', lightbox).addEventListener('click', function () { showLightbox(lbIndex + 1); });
    lightbox.addEventListener('click', function (e) { if (e.target === lightbox) closeLightbox(); });
    document.addEventListener('keydown', function (e) {
      if (!lightbox.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') showLightbox(lbIndex - 1);
      if (e.key === 'ArrowRight') showLightbox(lbIndex + 1);
    });
    // swipe
    let startX = 0;
    lightbox.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
    lightbox.addEventListener('touchend', function (e) {
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) showLightbox(lbIndex + (dx < 0 ? 1 : -1));
    });
  }
  function showLightbox(i) {
    if (!lightbox) buildLightbox();
    lbIndex = (i + lbItems.length) % lbItems.length;
    const item = lbItems[lbIndex];
    const img = $('img', lightbox);
    img.src = item.image;
    img.alt = item.title || 'Foto della galleria';
    $('h3', lightbox).textContent = item.title || '';
    $('p', lightbox).textContent = item.description || '';
    $('.lb-counter', lightbox).textContent = (lbIndex + 1) + ' / ' + lbItems.length;
    lightbox.classList.add('open');
    document.body.style.overflow = 'hidden';
    $('.lb-close', lightbox).focus();
  }
  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove('open');
    document.body.style.overflow = '';
  }

  function renderGallery(grid, items) {
    if (!grid) return;
    grid.innerHTML = '';
    lbItems = items;
    const frag = document.createDocumentFragment();

    items.forEach(function (item, i) {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'card reveal-scale';
      card.setAttribute('aria-label', 'Apri ' + (item.title || 'foto ' + (i + 1)));
      card.innerHTML =
        '<img src="' + escapeHtml(item.thumb) + '" alt="' + escapeHtml(item.title || 'Foto della galleria') + '"' +
          ' loading="lazy" decoding="async" referrerpolicy="no-referrer" draggable="false">' +
        '<span class="zoom" aria-hidden="true"><i class="fas fa-expand"></i></span>' +
        ((item.title || item.description)
          ? '<div class="card-caption">' +
              (item.title ? '<h3>' + escapeHtml(item.title) + '</h3>' : '') +
              (item.description ? '<p>' + escapeHtml(item.description) + '</p>' : '') +
            '</div>'
          : '');
      card.addEventListener('click', function () { showLightbox(i); });
      frag.appendChild(card);
    });

    grid.appendChild(frag);
    Array.from(grid.children).forEach(function (c, i) { c.style.setProperty('--i', i % 6); });
    observeReveal(grid);
  }

  /* Stato vuoto / errore della galleria, con rimando all'album */
  function renderGalleryEmpty(grid, message) {
    if (!grid) return;
    grid.innerHTML =
      '<div class="gallery-empty reveal is-visible">' +
        '<span class="ic"><i class="fas fa-images"></i></span>' +
        '<h3>La galleria si sta riempiendo</h3>' +
        '<p>' + escapeHtml(message) + '</p>' +
        '<a href="' + escapeHtml(decodeSecret('photos')) + '" class="btn btn-primary" target="_blank" rel="noopener">' +
          '<i class="fas fa-images"></i> Apri l\u2019album</a>' +
      '</div>';
  }

  function formatDate(iso) {
    try {
      return new Date(iso).toLocaleDateString('it-IT', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch (e) { return ''; }
  }

  function mapPhotosItems(data) {
    return (data.items || []).map(function (it) {
      return {
        image: it.image || '',
        thumb: it.thumb || it.image || '',
        title: it.title || '',
        description: it.description || ''
      };
    }).filter(function (it) { return !!it.image; });
  }

  function loadGallery(grid) {
    if (!grid) return;
    const src = grid.dataset.src || 'assets/data/photos.json';
    const limit = parseInt(grid.dataset.limit, 10);
    const meta = document.getElementById('gallery-meta');

    fetch(src + '?v=' + Math.floor(Date.now() / 300000), { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        const items = mapPhotosItems(data);
        if (!items.length) {
          renderGalleryEmpty(grid, 'Le prime foto stanno arrivando: intanto puoi aprire direttamente l\u2019album.');
          return;
        }
        renderGallery(grid, limit > 0 ? items.slice(0, limit) : items);
        if (meta) {
          meta.innerHTML = '<i class="fas fa-images"></i> ' + data.count + ' foto' +
            (data.updated ? ' · aggiornata il ' + escapeHtml(formatDate(data.updated)) : '');
        }
      })
      .catch(function () {
        renderGalleryEmpty(grid, 'Impossibile caricare la galleria in questo momento. Riprova tra poco.');
      });
  }

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
    loadGallery(document.getElementById('gallery-grid'));
  });
})();
