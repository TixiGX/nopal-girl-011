# Nopal Girl 🐎

Sito personale di **Althea — Nopal Girl**: passione per i cavalli e il salto ostacoli.
Sito statico in HTML, CSS e JavaScript puro, senza dipendenze né build step.

## Struttura

```
.
├── index.html                 Home: hero con video, storia, valori, album foto, social
├── gallery.html               Galleria: album condiviso di Google Foto + come funziona
├── social.html                Link ai profili social + contatto WhatsApp
└── assets/
    ├── css/style.css          Foglio di stile (design token in :root)
    ├── js/main.js             Nav, reveal, sparkles, link riservati, protezione, video
    └── videos/                Video hero e immagine poster
```

## Sviluppo locale

Non serve installare nulla. Per evitare limitazioni del protocollo `file://`
(font e icone da CDN, autoplay video) usa un server statico:

```bash
python3 -m http.server 8000
# oppure
npx serve .
```

Poi apri <http://localhost:8000>.

## Galleria con Google Foto

Le foto **non sono nel repository**: vivono in un album condiviso di Google Foto.
Il sito mostra una scheda «Apri l'album» che porta all'album: ogni foto aggiunta
all'album è subito visibile a chi apre il link, senza toccare il sito.

Per aggiungere foto basta aggiungerle all'album condiviso da telefono o computer
(app Google Foto → l'album → Aggiungi foto). Il link dell'album resta sempre lo stesso.

## Contatto WhatsApp

Il pulsante verde flottante in basso a sinistra, le icone social e i pulsanti
«Scrivimi» portano al contatto WhatsApp. Si apre la chat direttamente nell'app.

## Link riservati (offuscati)

I link sensibili (album Google Foto, contatto WhatsApp) **non compaiono in chiaro**
nel codice: sono salvati in forma codificata in `assets/js/main.js` (`SECRET_LINKS`)
e scritti negli `href` solo a runtime. Nell'HTML trovi solo `data-secret="photos"`
e `data-secret="whatsapp"`.

Per cambiare un link: codifica il nuovo URL in base64, dividilo in 3 parti e
sostituisci i pezzi in `SECRET_LINKS`:

```bash
echo -n 'NUOVO-URL' | base64
```

## Protezione dei contenuti

Il sito scoraggia la copia non autorizzata:

- tasto destro e long-press disabilitati (con avviso)
- trascinamento di immagini e video disabilitato
- copia/taglia disabilitati (con avviso)
- scorciatoie di ispezione/salvataggio/stampa bloccate (F12, Ctrl+U/S/P, …)
- stampa: mostra solo un avviso di copyright
- nota di copyright nel footer («Vietata la riproduzione anche parziale»)

> Nota onesta: nessuna protezione lato client è efficace al 100% contro un utente
> esperto, ma ferma la copia occasionale e chiarisce che i contenuti sono protetti.

## Aggiornare i link social

Gli URL `.../nopalgirl` sono placeholder. Cercali e sostituiscili con i profili reali
(`grep -rn nopalgirl *.html`): compaiono nella nav, nella sezione social, nelle card di
`social.html`, nel footer e nel JSON-LD di `index.html`.

## Deploy

Essendo un sito statico può essere pubblicato così com'è su GitHub Pages,
Netlify, Vercel, Cloudflare Pages o qualsiasi hosting statico, con `index.html`
alla radice del repository.

## Licenza

© 2026 Nopal Girl — Tutti i diritti riservati. Vedi [LICENSE](LICENSE).

Questo progetto è **privato e proprietario**: nessun uso, copia, modifica o
distribuzione — anche parziale — è consentita senza autorizzazione scritta
della proprietaria.
