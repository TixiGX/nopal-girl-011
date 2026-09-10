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
│   ├── images/           Illustrazioni galleria (gallery-01..06.jpg) e ritratto
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

Metti la foto in `assets/images/` e aggiungi una voce in `assets/js/gallery-data.js`:

```js
{ image: 'assets/images/mia-foto.jpg', size: 'wide', tag: 'Gara',
  icon: '🏇', title: 'Titolo', description: 'Didascalia breve' }
```

- `size`: `''` (1 cella), `'wide'` (2 colonne) o `'tall'` (2 righe) per il mosaico
- `image` vuoto → viene mostrata l'`icon` come segnaposto
- Le immagini si aprono in una lightbox (frecce ← →, swipe su mobile, Esc per chiudere)
- La home mostra le prime 3 voci (`data-limit="3"` su `#gallery-grid`), la galleria tutte

> Le illustrazioni attuali sono segnaposto generati nello stile del poster del video:
> sostituiscile con le foto vere quando disponibili.

## Aggiornare i link social

Gli URL `.../nopalgirl` sono placeholder. Cercali e sostituiscili con i profili reali
(`grep -rn nopalgirl *.html`): compaiono nella nav, nella sezione social, nelle card di
`social.html`, nel footer e nel JSON-LD di `index.html`.

## Deploy

Essendo un sito statico può essere pubblicato così com'è su GitHub Pages,
Netlify, Vercel, Cloudflare Pages o qualsiasi hosting statico, con `index.html`
alla radice del repository.

## Licenza

[Apache 2.0](LICENSE)
