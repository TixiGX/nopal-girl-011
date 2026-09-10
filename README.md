# Nopal Girl 🐎

Sito personale di **Althea — Nopal Girl**: passione per i cavalli e il salto ostacoli.
Sito statico in HTML, CSS e JavaScript puro, senza dipendenze né build step.

## Struttura

```
.
├── index.html                 Home: hero con video, storia, valori, galleria foto, social
├── gallery.html               Galleria completa dall'album Google Foto
├── social.html                Link ai profili social + contatto WhatsApp
├── scripts/
│   └── sync_photos.py         Legge l'album Google Foto e rigenera photos.json
├── .github/workflows/
│   └── sync-photos.yml        Sync automatico ogni 6 ore + avvio manuale
└── assets/
    ├── css/style.css          Foglio di stile (design token in :root)
    ├── js/main.js             Nav, reveal, galleria + lightbox, link riservati, protezione
    ├── data/photos.json       Elenco foto, generato dallo script di sync
    └── videos/                Video hero e immagine poster
```

## Sviluppo locale

Non serve installare nulla. Per evitare limitazioni del protocollo `file://`
(fetch del JSON, font e icone da CDN, autoplay video) usa un server statico:

```bash
python3 -m http.server 8000
# oppure
npx serve .
```

Poi apri <http://localhost:8000>.

## Galleria automatica da Google Foto

Le foto **non sono nel repository**: vivono nell'album condiviso di Google Foto
e il sito le mostra direttamente nella griglia, con lightbox per ingrandirle
(clic, frecce, swipe).

Ogni 6 ore (più avvio manuale) il workflow **Sync foto da Google Foto** legge
l'album e aggiorna `assets/data/photos.json` con gli URL diretti delle foto.
Le immagini restano sui server di Google, quindi il repository non si appesantisce.
Il commit avviene solo se ci sono novità.

Configurazione una tantum:

1. Su GitHub → *Settings → Secrets and variables → Actions* crea il secret
   `PHOTOS_ALBUM_URL` con il link di condivisione dell'album (quello che inizia
   con `https://photos.app.goo.gl/...`). Senza secret il workflow fallisce.
2. Aggiungi foto all'album da telefono o computer (app Google Foto → l'album →
   Aggiungi foto). L'album deve restare condiviso «chiunque abbia il link».
3. Tab *Actions* → «Sync foto da Google Foto» → **Run workflow**. Da lì in poi
   gira da solo ogni 6 ore.

Per lanciare il sync a mano dal PC (solo libreria standard, nulla da installare):

```bash
PHOTOS_ALBUM_URL='...' python3 scripts/sync_photos.py
```

> Il link dell'album non compare mai nel codice: nel sito è offuscato
> (`SECRET_LINKS` in `assets/js/main.js`), nel workflow vive nel secret.

Limiti noti: vengono lette le foto presenti nella pagina iniziale dell'album
(basta per album personali fino a ~100 foto); titoli e descrizioni delle foto
non vengono importati.

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
