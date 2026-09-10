# Nopal Girl 🐎

Sito personale di **Althea — Nopal Girl**: passione per i cavalli e il salto ostacoli.
Sito statico in HTML, CSS e JavaScript puro, senza dipendenze né build step.

## Struttura

```
.
├── index.html                 Home: hero con video, storia, valori, anteprima galleria, social
├── gallery.html               Galleria completa (foto dal gruppo Telegram)
├── social.html                Link ai profili social
├── assets/
│   ├── css/style.css          Foglio di stile (design token in :root)
│   ├── js/main.js             Nav, reveal, galleria (fetch del JSON), lightbox, video
│   ├── data/gallery.json      Indice della galleria, generato dallo script di sync
│   ├── images/telegram/       Foto scaricate da Telegram (generate, non toccare a mano)
│   └── videos/                Video hero e immagine poster
├── scripts/
│   ├── sync_telegram.py       Scarica le foto dal gruppo e rigenera gallery.json
│   ├── telegram_login.py      Genera una volta la sessione Telegram (TG_SESSION)
│   └── requirements.txt       Dipendenze Python (Telethon)
└── .github/workflows/
    └── sync-telegram.yml      Sync automatico ogni 6 ore + avvio manuale
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

Le foto della galleria **non si caricano a mano**: arrivano dal gruppo Telegram
[Gallery](https://t.me/+gjZgJrg2KqRkOWE0). Ogni foto pubblicata nel gruppo viene
scaricata in `assets/images/telegram/`, indicizzata in `assets/data/gallery.json`
e mostrata sul sito (la didascalia del messaggio diventa titolo + descrizione:
prima riga = titolo, righe successive = descrizione). Le foto cancellate dal
gruppo spariscono anche dal sito al sync successivo.

Il gruppo è privato, quindi Telegram non espone le foto pubblicamente: serve
un account membro del gruppo che faccia da "lettore". Configurazione una tantum:

1. Vai su <https://my.telegram.org/apps> con l'account che è nel gruppo e crea
   un'app: ottieni **API ID** e **API hash**.
2. In locale genera la sessione (chiede telefono e codice ricevuto su Telegram):
   ```bash
   pip install -r scripts/requirements.txt
   python3 scripts/telegram_login.py
   ```
3. Su GitHub → *Settings → Secrets and variables → Actions* crea i **secrets**:
   `TG_API_ID`, `TG_API_HASH`, `TG_SESSION` (la stringa stampata al punto 2).
   Facoltativo: la *variable* `TG_CHAT` se il gruppo cambia link.
4. Tab *Actions* → "Sync galleria da Telegram" → **Run workflow**. Da lì in poi
   gira da solo ogni 6 ore e committa solo se ci sono novità.

Per lanciare il sync a mano dal PC:

```bash
TG_API_ID=... TG_API_HASH=... TG_SESSION=... python3 scripts/sync_telegram.py
```

> Non committare mai `TG_SESSION` o file `*.session`: sono già in `.gitignore`.

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
