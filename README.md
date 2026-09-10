# Nopal Girl 🐎

Sito personale di **Althea — Nopal Girl**: passione per i cavalli e il salto ostacoli.
Sito statico in HTML, CSS e JavaScript puro, senza dipendenze né build step.

## Struttura

```
.
├── index.html                 Home: hero con video, storia, valori, galleria foto, social
├── gallery.html               Galleria completa alimentata dal canale Telegram
├── social.html                Link ai profili social + contatto WhatsApp
├── scripts/
│   ├── sync_telegram.py       Legge il canale Telegram, scarica le foto e rigenera photos.json
│   └── upscale_media.py       Porta foto e video in 4K (e i video a 60 fps) + varianti responsive
├── .github/workflows/
│   └── sync-telegram.yml      Sync automatico ogni 20 minuti + avvio manuale
└── assets/
    ├── css/style.css          Foglio di stile (design token in :root)
    ├── js/main.js             Nav, reveal, galleria + lightbox, link riservati, protezione
    ├── data/photos.json       Elenco foto, generato dallo script di sync
    ├── images/telegram/       Foto scaricate dal canale (committate dal workflow)
    └── videos/                Video hero 4K 60fps e immagine poster 4K (+ varianti responsive)
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

## Galleria automatica da Telegram

Il canale Telegram fa da "archivio foto": **ogni foto pubblicata sul canale
finisce nella galleria del sito**, in automatico. Le didascalie del post
diventano titolo (prima riga breve) e descrizione della foto; gli album con più
scatti sono supportati.

Come funziona il sync:

- ogni 20 minuti (più avvio manuale e a ogni aggiornamento di `main`) il
  workflow **Sync galleria da Telegram** esegue `scripts/sync_telegram.py`;
- per i canali **pubblici** legge l'anteprima pubblica `t.me/<canale>`:
  recupera anche **tutto lo storico** al primo giro, non solo le foto recenti,
  e rileva quando una foto viene cancellata dal canale;
- il token del bot serve per i canali **privati** (via Bot API) e per trovare
  il canale da solo;
- le immagini vengono scaricate in `assets/images/telegram/` e registrate in
  `assets/data/photos.json`, poi il workflow committa tutto (solo se ci sono
  novità). Così le foto sono ospitate dal sito, senza URL che scadono.

Configurazione una tantum:

1. Crea un bot con [@BotFather](https://t.me/BotFather) se non l'hai già fatto.
2. Aggiungi il bot al canale come **amministratore** (basta il permesso di
   pubblicare/vedere i post: è così che riceve le foto).
3. Su GitHub → *Settings → Secrets and variables → Actions* crea un secret
   chiamato **`TELEGRAM_BOT_TOKEN`** con il token del bot (il workflow accetta
   anche `TELEGRAM_TOKEN`, `BOT_TOKEN` o `TELEGRAM_BOT_KEY`).
4. (Facile ma opzionale) Se il canale è pubblico aggiungi nella stessa pagina,
   scheda *Variables*, la variabile **`TELEGRAM_CHANNEL`** con lo username
   (es. `@nome_canale`). Se non la metti, il canale viene rilevato da solo dal
   primo post che il bot vede. Per un canale privato metti invece il suo id
   numerico `-100...`.
5. Tab *Actions* → **Sync galleria da Telegram** → *Run workflow*.
   Da lì in poi gira da solo ogni 20 minuti.

Per provare il sync a mano dal PC (solo libreria standard, nulla da installare):

```bash
# canale pubblico: basta lo username, il token non è nemmeno obbligatorio
TELEGRAM_CHANNEL='@nome_canale' python3 scripts/sync_telegram.py

# canale privato / auto-rilevamento: serve il token del bot
TELEGRAM_BOT_TOKEN='123456:ABC...' python3 scripts/sync_telegram.py
```

> I link "Apri il canale Telegram" nel sito non sono hardcodati: il loro URL
> (`source_url`) viene scritto nello stesso `photos.json` dal sync, quindi il
> canale si può rinominare senza toccare il codice.

Limiti noti:

- il canale deve avere l'anteprima pubblica abilitata (default) per scaricare
  lo storico via web; in caso contrario si usano gli aggiornamenti del bot,
  che coprono le ultime 24 ore;
- con i canali privati l'eliminazione di un vecchio post non viene rilevata;
- vengono importate le foto, non i video.

## Media in 4K (foto e video)

Tutte le foto e tutti i video del progetto sono **in 4K**, e i video girano a
**60 fps**:

- **Foto** — super-risoluzione AI (Real-ESRGAN x4plus) fino a **3840x2160**:
  il modello ricostruisce dettagli reali (soggetti e volti restano gli stessi,
  solo più nitidi). Da ogni master vengono generate le varianti responsive
  WebP/JPEG a **3840 / 2560 / 1920 / 1280 px**, dichiarate nelle pagine con
  `srcset`/`sizes`: un telefono scarica la versione giusta, il master 4K resta
  il fallback (ed è quello usato come `og:image`).
- **Video** — `assets/videos/video.mp4` è **3840x2160 @ 60 fps** (~5 MB):
  leggera riduzione del rumore, interpolazione dei fotogrammi con stima del
  movimento (da 24 a 60 fps), ingrandimento Lanczos e sharpening finale, poi
  codifica H.264 "compressa al massimo" (CRF 30).

Per rigenerare gli asset dopo aver sostituito una foto o un video:

```bash
pip install pillow ncnn sr-vulkan-model-realesrgan imageio-ffmpeg
python3 scripts/upscale_media.py             # foto + video + varianti
python3 scripts/upscale_media.py --only video
python3 scripts/upscale_media.py --dry-run   # anteprima, non tocca i file
```

Note utili:

- lo script serve solo a chi rigenera i media: il sito resta statico e non ha
  dipendenze. Se `ncnn`/Real-ESRGAN mancano, le foto vengono comunque portate
  a 4K con Lanczos (senza guadagno di dettaglio);
- l'upscaling AI gira su CPU: contare ~2 minuti per foto su 2 core;
- le foto che arrivano dal canale Telegram **non** vengono upscalate in
  automatico dal workflow: per farlo basta lanciare
  `python3 scripts/upscale_media.py` dopo un sync e committare il risultato;
- se in futuro il video 4K risultasse troppo pesante sul traffico mobile, si
  può riaggiungere una copia 1080p/720p come `<source>` alternativo.

## Contatto WhatsApp

Il pulsante verde flottante in basso a sinistra, le icone social e i pulsanti
«Scrivimi» portano al contatto WhatsApp. Si apre la chat direttamente nell'app.

## Link riservati (offuscati)

Gli URL sensibili **non compaiono in chiaro** nel codice:

- il contatto WhatsApp è codificato in `assets/js/main.js` (`SECRET_LINKS`) e
  scritto negli `href` solo a runtime (`data-secret="whatsapp"`);
- il link del canale Telegram (`data-secret="photos"`) viene letto a runtime da
  `assets/data/photos.json` (`source_url`), generato dallo script di sync.

Per cambiare il link WhatsApp: codifica il nuovo URL in base64, dividilo in
3 parti e sostituisci i pezzi in `SECRET_LINKS`:

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
