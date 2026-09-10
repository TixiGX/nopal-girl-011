/* ============================================================
   Nopal Girl — shared scripts (lightweight, no dependencies)
   ============================================================ */
(function () {
  'use strict';

  /* ---------- Navigation: scroll state + mobile menu ---------- */
  const nav = document.querySelector('.nav');
  const toggle = document.querySelector('.mobile-toggle');
  const links = document.querySelector('.nav-links');
  const navLinks = document.querySelectorAll('.nav-links a');

  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      if (nav) nav.classList.toggle('scrolled', window.scrollY > 30);
      if (links) links.classList.remove('open');
      if (toggle) toggle.classList.remove('open');
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });

  if (toggle && links) {
    toggle.addEventListener('click', function () {
      const open = links.classList.toggle('open');
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    });
  }
  navLinks.forEach(function (a) {
    a.addEventListener('click', function () {
      if (links) links.classList.remove('open');
      if (toggle) toggle.classList.remove('open');
    });
  });

  /* ---------- Reveal-on-scroll (IntersectionObserver) ---------- */
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- CSS-only sparkle dust (cheap, no setInterval storm) ---------- */
  function buildSparkles(n) {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;
    const host = document.createElement('div');
    host.className = 'sparkles';
    host.setAttribute('aria-hidden', 'true');
    const frag = document.createDocumentFragment();
    for (let i = 0; i < n; i++) {
      const s = document.createElement('span');
      s.className = 'sparkle';
      s.style.left = Math.random() * 100 + 'vw';
      s.style.width = (Math.random() * 4 + 2) + 'px';
      s.style.height = s.style.width;
      const dur = Math.random() * 8 + 10;
      s.style.animationDuration = dur + 's';
      s.style.animationDelay = Math.random() * -dur + 's';
      frag.appendChild(s);
    }
    host.appendChild(frag);
    document.body.appendChild(host);
  }
  buildSparkles(16);

  /* ---------- Gallery renderer (data-driven, lazy placeholders) ---------- */
  function renderGallery(grid, items) {
    if (!grid) return;
    items.forEach(function (item) {
      const card = document.createElement('article');
      card.className = 'card reveal';

      const media = document.createElement('div');
      media.className = 'card-media';
      media.innerHTML =
        '<span class="placeholder" aria-hidden="true">' + item.icon + '</span>' +
        (item.image
          ? '<img src="' + item.image + '" alt="' + item.title +
            '" loading="lazy" decoding="async">'
          : '');

      const body = document.createElement('div');
      body.className = 'card-body';
      body.innerHTML =
        '<h3>' + item.title + '</h3><p>' + item.description + '</p>';

      card.appendChild(media);
      card.appendChild(body);
      grid.appendChild(card);
    });

    // Reveal newly added cards
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });
      grid.querySelectorAll('.card').forEach(function (c) { io.observe(c); });
    }
  }

  /* ---------- Hero video autoplay fallback ---------- */
  function initVideo() {
    const video = document.querySelector('.hero-video video');
    if (!video) return;
    const play = function () {
      const p = video.play();
      if (p && typeof p.catch === 'function') {
        p.catch(function () {
          // Autoplay blocked — rely on the poster image instead.
          const poster = document.querySelector('.hero-video img.poster');
          if (poster) poster.style.display = 'block';
        });
      }
    };
    video.addEventListener('canplay', play);
    if (video.readyState >= 3) play();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initVideo();
    const grid = document.getElementById('gallery-grid');
    if (grid && window.NOPAL_GALLERY) {
      renderGallery(grid, window.NOPAL_GALLERY);
    }
  });
})();