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

  /* ---------- Gallery renderer + lightbox ---------- */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
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
      '<figure><img alt=""><figcaption><h3></h3><p></p></figcaption></figure>' +
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
    img.alt = item.title;
    $('h3', lightbox).textContent = item.title || '';
    $('p', lightbox).textContent = [item.description, item.tag].filter(Boolean).join(' · ');
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
      card.className = 'card reveal-scale' + (item.size ? ' ' + item.size : '');
      card.setAttribute('aria-label', 'Apri ' + (item.title || 'foto ' + (i + 1)));
      card.innerHTML =
        '<img src="' + escapeHtml(item.image) + '" alt="' + escapeHtml(item.title || 'Foto della galleria') + '"' +
          (item.width && item.height ? ' width="' + item.width + '" height="' + item.height + '"' : '') +
          ' loading="lazy" decoding="async">' +
        '<span class="zoom" aria-hidden="true"><i class="fas fa-expand"></i></span>' +
        ((item.title || item.description || item.tag)
          ? '<div class="card-caption">' +
              (item.tag ? '<span class="tag">' + escapeHtml(item.tag) + '</span>' : '') +
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

  /* Stato vuoto / errore della galleria */
  function renderGalleryEmpty(grid, message) {
    if (!grid) return;
    grid.innerHTML =
      '<div class="gallery-empty reveal is-visible">' +
        '<span class="ic"><i class="fab fa-telegram"></i></span>' +
        '<h3>La galleria si sta riempiendo</h3>' +
        '<p>' + escapeHtml(message) + '</p>' +
      '</div>';
  }

  function formatDate(iso) {
    try {
      return new Date(iso).toLocaleDateString('it-IT', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch (e) { return ''; }
  }

  /* Trasforma le voci del JSON in item per la griglia.
     size: dal rapporto d'aspetto reale della foto (panoramica → wide, verticale → tall). */
  function mapTelegramItems(data) {
    return (data.items || []).map(function (it) {
      const ratio = it.width && it.height ? it.width / it.height : 1;
      return {
        image: it.file,
        title: it.title || '',
        description: it.description || '',
        tag: it.date ? formatDate(it.date) : '',
        width: it.width, height: it.height,
        size: ratio >= 1.45 ? 'wide' : ratio <= 0.8 ? 'tall' : ''
      };
    });
  }

  function loadGallery(grid) {
    if (!grid) return;
    const src = grid.dataset.src || 'assets/data/gallery.json';
    const limit = parseInt(grid.dataset.limit, 10);
    const meta = document.getElementById('gallery-meta');

    fetch(src + '?v=' + Math.floor(Date.now() / 300000), { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) {
        let items = mapTelegramItems(data);
        if (!items.length) {
          renderGalleryEmpty(grid, 'Le prime foto arriveranno presto dal gruppo Telegram.');
          return;
        }
        if (limit > 0) {
          items = items.slice(0, limit);
          // in anteprima niente celle alte: griglia compatta
          items.forEach(function (it) { if (it.size === 'tall') it.size = ''; });
        }
        renderGallery(grid, items);
        if (meta && data.updated) {
          meta.innerHTML = '<i class="fab fa-telegram"></i> ' + data.count + ' foto · aggiornata il ' + escapeHtml(formatDate(data.updated));
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
    loadGallery(document.getElementById('gallery-grid'));
  });
})();
