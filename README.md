# Nopal Girl 🐎

Sito personale di **Althea — Nopal Girl**: passione per i cavalli e il salto ostacoli.
Sito statico in HTML, CSS e JavaScript puro, senza dipendenze né build step.

## Struttura

```
.
├── index.html            Home: hero con video, anteprima galleria, social
├── gallery.html          Galleria completa
├── social.html           Link ai profili social
├── assets/
│   ├── css/style.css     Foglio di stile (design token in :root)
│   ├── js/main.js        Nav, menu mobile, reveal-on-scroll, render galleria, video
│   ├── js/gallery-data.js  Dati della galleria (unica fonte per home e galleria)
│   └── videos/           Video hero e immagine poster
├── LICENSE               Apache 2.0
└── README.md
```

## Sviluppo locale

Non serve installare nulla. Per evitare limitazioni del protocollo `file://`
(font e icone da CDN, autoplay video) è consigliato un server statico:

```bash
python3 -m http.server 8000
# oppure
npx serve .
```

Poi apri <http://localhost:8000>.

## Aggiungere foto alla galleria

Modifica `assets/js/gallery-data.js`: ogni voce ha `icon`, `title`, `description`
e `image`. Inserisci in `image` il percorso della foto (es. `assets/images/salto-01.jpg`);
finché è vuoto viene mostrata l'icona come segnaposto. La home mostra automaticamente
le prime 3 voci (`data-limit="3"` su `#gallery-grid`), la galleria le mostra tutte.

## Aggiornare i link social

I link si trovano in `index.html` e `social.html` (blocco `.social-icons`):
sostituisci gli URL `.../nopalgirl` con i profili reali.

## Deploy

Essendo un sito statico può essere pubblicato così com'è su GitHub Pages,
Netlify, Vercel, Cloudflare Pages o qualsiasi hosting statico, con `index.html`
alla radice del repository.

## Licenza

[Apache 2.0](LICENSE)
