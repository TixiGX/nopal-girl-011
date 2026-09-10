#!/usr/bin/env python3
"""
Sincronizza la galleria del sito con un canale Telegram.

Ogni foto pubblicata sul canale viene scaricata nel repository e registrata
in assets/data/photos.json, che il sito mostra nella pagina Galleria.

Fonti delle foto:
  1. Anteprima pubblica https://t.me/s/<username>  -> storico completo del
     canale (le foto vecchie vengono recuperate al primo giro) ed è anche
     il modo con cui vengono viste le nuove foto a ogni esecuzione.
  2. Bot API (getUpdates)                           -> necessaria per i
     canali privati (senza username) e per rilevare da sola il canale.

Prerequisito: il bot deve essere amministratore del canale (così riceve
tutti i post). Niente sessioni utente né Telethon: basta il token del bot.

Uso locale:
    TELEGRAM_BOT_TOKEN='123456:ABC...' python3 scripts/sync_telegram.py
    TELEGRAM_CHANNEL='@nome_canale' python3 scripts/sync_telegram.py   # pubblico,
                                                                       # senza token

Variabili d'ambiente:
    TELEGRAM_BOT_TOKEN   token del bot (accetta anche TELEGRAM_TOKEN,
                         BOT_TOKEN o TELEGRAM_BOT_KEY)
    TELEGRAM_CHANNEL     username (@nome o nome) oppure id numerico -100...
                         Se assente viene rilevato da solo dai getUpdates
    TG_MAX_PHOTOS        massimo numero di foto da tenere (default 200)

Solo libreria standard: nessuna dipendenza da installare.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "images" / "telegram"
JSON_PATH = ROOT / "assets" / "data" / "photos.json"

TOKEN = (
    os.environ.get("TELEGRAM_BOT_TOKEN")
    or os.environ.get("TELEGRAM_TOKEN")
    or os.environ.get("BOT_TOKEN")
    or os.environ.get("TELEGRAM_BOT_KEY")
    or ""
).strip()
CHANNEL_CONF = os.environ.get("TELEGRAM_CHANNEL", "").strip()
MAX_PHOTOS = int(os.environ.get("TG_MAX_PHOTOS", "200"))
POLL_TIMEOUT = int(os.environ.get("TG_POLL_TIMEOUT", "20"))
API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
WEB_BASE = os.environ.get("TELEGRAM_WEB_BASE", "https://t.me").rstrip("/")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept-Encoding": "identity",
}


def die(msg: str) -> None:
    print(f"ERRORE: {msg}", file=sys.stderr)
    sys.exit(1)


def http_get(url: str, binary: bool = False, referer: str = ""):
    headers = dict(UA)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def bot_call(method: str, **params):
    if not TOKEN:
        die(
            "imposta TELEGRAM_BOT_TOKEN con il token del bot "
            "(su GitHub: Settings -> Secrets and variables -> Actions)"
        )
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{API_BASE}/bot{TOKEN}/{method}?{qs}"
    try:
        raw = http_get(url)
    except Exception as e:  # noqa: BLE001 - fallisce il workflow con messaggio chiaro
        die(f"chiamata {method} fallita: {e}")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        die(f"risposta non JSON da {method}: {raw[:200]}")
    if not payload.get("ok"):
        die(f"Telegram {method}: {payload.get('description')}")
    return payload.get("result")


# ------------------------------------------------------------ manifest
def load_manifest() -> dict:
    if JSON_PATH.exists():
        try:
            data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return data
        except json.JSONDecodeError:
            pass
    return {"updated": None, "source": None, "source_url": None,
            "count": 0, "items": []}


def item_num_id(iid: str) -> int:
    try:
        return int(str(iid).split("-")[0])
    except (ValueError, IndexError):
        return 0


def split_caption(text: str):
    """Prima riga breve -> titolo, il resto -> descrizione."""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return "", ""
    if len(lines) > 1 and len(lines[0]) <= 80:
        return lines[0], " ".join(lines[1:])[:400]
    return "", " ".join(lines)[:400]


def clean_html(fragment: str) -> str:
    fragment = re.sub(r"(?i)<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"(?i)</(p|div|li)>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in fragment.splitlines()]
    return "\n".join([ln for ln in lines if ln])


# ------------------------------------------------------------ t.me/s scraping
POST_RE = re.compile(
    r'<div[^>]*class="[^"]*tgme_widget_message\b[^"]*"[^>]*data-post="([^"]+)"',
    re.S,
)
PHOTO_RE = re.compile(
    r'<a[^>]*class="[^"]*tgme_widget_message_photo_wrap\b[^"]*"[^>]*>', re.S
)
STYLE_URL_RE = re.compile(r"background-image:\s*url\((['\"]?)(.*?)\1\)", re.S)
TEXT_RE = re.compile(
    r'<div[^>]*class="[^"]*tgme_widget_message_text\b[^"]*"[^>]*>(.*?)</div>',
    re.S,
)
TIME_RE = re.compile(r'<time[^>]*datetime="([^"]+)"')


def parse_post_block(block: str):
    """Estrae (url_foto, didascalia, data) da un blocco-messaggio di t.me/s."""
    # La data sta nella riga info in fondo al blocco: la leggiamo prima di
    # scartare l'eventuale anteprima di un link, che contiene immagini Sue
    date = ""
    dm = TIME_RE.search(block)
    if dm:
        date = dm.group(1)
    # L'anteprima dei link contiene immagini sue: la scartiamo a priori
    block = re.sub(
        r'<div[^>]*class="[^"]*tgme_widget_message_link_preview\b.*',
        "",
        block,
        flags=re.S,
    )
    photos = []
    for tag in PHOTO_RE.findall(block):
        m = STYLE_URL_RE.search(tag)
        if m:
            photos.append(html.unescape(m.group(2)))
    text = ""
    tm = TEXT_RE.search(block)
    if tm:
        text = clean_html(tm.group(1))
    return photos, text, date


def scrape_channel(username: str, stop_at_id: int = 0):
    """Sfoglia l'anteprima pubblica andando indietro nel tempo.

    Ritorna (posts, titolo, floor_id):
      posts   dict msg_id -> {'urls': [...], 'text': str, 'date': str}
      floor_id il msg_id piu' vecchio coperto (per le cancellazioni)
    """
    uname = username.lstrip("@")
    posts = {}
    title = None
    before = None
    floor_id = 0

    for _ in range(30):  # massimo 30 pagine (~600 post)
        url = f"{WEB_BASE}/s/{uname}"
        if before is not None:
            url += f"?before={before}"
        try:
            page = http_get(url, referer=f"{WEB_BASE}/{uname}")
        except Exception as e:  # noqa: BLE001
            print(f"AVVISO: anteprima pubblica non disponibile ({e}); "
                  "uso solo la Bot API.", file=sys.stderr)
            break

        if title is None:
            mt = re.search(
                r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', page
            )
            if mt:
                title = html.unescape(mt.group(1)).strip()

        matches = list(POST_RE.finditer(page))
        seen_mids = set()
        page_min = None
        for i, m in enumerate(matches):
            post_ref = m.group(1)  # forma 'nomecanale/12345'
            try:
                mid = int(post_ref.rsplit("/", 1)[1])
            except (ValueError, IndexError):
                continue
            seen_mids.add(mid)
            page_min = mid if page_min is None else min(page_min, mid)
            if mid in posts:
                continue
            end = matches[i + 1].start() if i + 1 < len(matches) else len(page)
            block = page[m.start():end]
            photos, text, date = parse_post_block(block)
            if photos:
                posts[mid] = {"urls": photos, "text": text, "date": date}

        if not matches or not seen_mids:
            break  # canale vuoto o fine della storia
        floor_id = page_min if not floor_id else min(floor_id, page_min)
        if stop_at_id and page_min <= stop_at_id:
            break  # storico gia' presente nel manifest
        before = page_min

    return posts, title, floor_id


# ------------------------------------------------------------ Bot API
def poll_updates():
    """Tutti gli aggiornamenti appesi (channel_post, anche modificati)."""
    if not TOKEN:
        return []
    bot_call("deleteWebhook")  # altrimenti getUpdates restituisce 409
    updates = bot_call(
        "getUpdates", timeout=POLL_TIMEOUT, limit=100,
        allowed_updates='["channel_post","edited_channel_post"]',
    )
    return updates or []


def updates_to_posts(updates):
    """Converte gli update in posts {mid: {...}} + info sul canale."""
    posts = {}
    chat_info = None
    last_update_id = None
    for upd in updates:
        last_update_id = upd["update_id"]
        msg = upd.get("channel_post") or upd.get("edited_channel_post")
        if not msg or "photo" not in msg:
            continue
        chat = msg.get("chat", {})
        mid = msg.get("message_id")
        if mid is None:
            continue
        sizes = sorted(msg["photo"], key=lambda s: s.get("width", 0))
        full = sizes[-1]
        thumb = min(sizes, key=lambda s: abs(s.get("width", 0) - 480))
        date = datetime.fromtimestamp(msg.get("date", 0),
                                      tz=timezone.utc).isoformat(timespec="seconds")
        posts[mid] = {
            "text": msg.get("caption", ""),
            "date": date,
            "full": full,
            "thumb": thumb if thumb is not full else None,
        }
        if chat_info is None:
            chat_info = {
                "id": chat.get("id"),
                "username": (chat.get("username") or "").lstrip("@"),
                "title": chat.get("title") or "",
            }
    return posts, chat_info, last_update_id


def bot_download(file_id: str, base: Path):
    """Scarica un file tramite getFile. Ritorna (Path, nuovo_download?) o None."""
    info = bot_call("getFile", file_id=file_id)
    remote = info.get("file_path", "")
    if not remote:
        return None
    ext = os.path.splitext(remote)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    dest = base.with_suffix(ext)
    if dest.exists() and dest.stat().st_size > 0:
        return dest, False
    url = f"{API_BASE}/file/bot{TOKEN}/{remote}"
    dest.write_bytes(http_get(url, binary=True))
    return dest, True


def http_download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.write_bytes(http_get(url, binary=True, referer=WEB_BASE + "/"))
    return dest


def channel_source_url(username: str, chat_id) -> str:
    if username:
        return f"https://t.me/{username}"
    if isinstance(chat_id, int) and str(chat_id).startswith("-100"):
        return f"https://t.me/c/{str(chat_id)[4:]}"
    return ""


def main() -> None:
    manifest = load_manifest()
    existing = {it["id"]: it for it in manifest.get("items", [])}

    # 1) Canale: configurazione esplicita oppure auto-rilevamento dal bot
    updates = poll_updates()
    bot_posts, discovered, last_update_id = updates_to_posts(updates)

    username = ""
    chat_id = None
    source_title = ""
    if CHANNEL_CONF:
        if CHANNEL_CONF.lstrip("-").isdigit():
            chat_id = int(CHANNEL_CONF)
        else:
            username = CHANNEL_CONF.lstrip("@")
    elif discovered:
        username = discovered.get("username") or ""
        chat_id = discovered.get("id")
        source_title = discovered.get("title") or ""
    elif not TOKEN:
        die("imposta TELEGRAM_CHANNEL=@nomecanale (o TELEGRAM_BOT_TOKEN)")
    else:
        # Niente di rotto: il bot semplicemente non vede ancora nessun
        # canale. Lasciamo la galleria vuota (il sito sa mostrare lo stato
        # di attesa) invece di fallire il job a ogni esecuzione.
        print(
            "AVVISO: il bot non vede ancora nessun canale. Aggiungilo come "
            "amministratore del canale e pubblica una foto (oppure imposta "
            "la variabile TELEGRAM_CHANNEL con @username o l'id -100...). "
            "Galleria lasciata vuota.",
            file=sys.stderr,
        )
        JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        JSON_PATH.write_text(
            json.dumps(
                {
                    "source": None,
                    "source_url": None,
                    "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "count": 0,
                    "items": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return

    # 2) Storico e novita' dall'anteprima pubblica (canale con username).
    #    Il piu' vecchio id gia' in archivio fa da fermo all'impaginazione.
    stop_at = min((item_num_id(i) for i in existing), default=0)
    scraped, scraped_title, floor_id = (
        scrape_channel(username, stop_at) if username else ({}, None, 0)
    )
    if scraped_title:
        source_title = scraped_title
    if not chat_id and discovered:
        chat_id = discovered.get("id")
    if not source_title:
        source_title = f"@{username}" if username else "Canale Telegram"
    source_url = channel_source_url(username, chat_id)

    # Il bot fa da fonte solo se l'anteprima pubblica non c'e' (canale
    # privato, preview disattivata, errore di rete): evita doppioni degli
    # album, che sul web sono un widget unico e via bot messaggi separati.
    use_bot = not username or not scraped
    if use_bot and not TOKEN:
        die("serve TELEGRAM_BOT_TOKEN per leggere un canale privato")

    # 3) Download e costruzione degli item
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    items = dict(existing)
    seen_ids = set()  # id presenti sul canale durante QUESTO giro
    downloaded = 0

    def rel(path: Path) -> str:
        return path.relative_to(ROOT).as_posix()

    def upsert(mid: int, idx: int, title: str, desc: str, date: str,
               image_path: Path, thumb_path: Path):
        iid = f"{mid}-{idx}"
        items[iid] = {
            "id": iid,
            "image": rel(image_path),
            "thumb": rel(thumb_path),
            "title": title,
            "description": desc,
            "date": date,
            "post_url": (
                f"https://t.me/{username}/{mid}" if username
                else channel_source_url("", chat_id) + f"/{mid}"
                if chat_id and str(chat_id).startswith("-100") else ""
            ),
        }
        seen_ids.add(iid)

    for mid, post in scraped.items():
        title, desc = split_caption(post["text"])
        for idx, url in enumerate(post["urls"]):
            dest = IMG_DIR / f"tg_{mid}_{idx}.jpg"
            try:
                before_ok = dest.exists()
                path = http_download(url, dest)
                downloaded += int(not before_ok and path.exists())
            except Exception as e:  # noqa: BLE001
                print(f"AVVISO: foto {mid}-{idx} non scaricata: {e}",
                      file=sys.stderr)
                continue
            upsert(mid, idx, title, desc, post["date"], path, path)

    if use_bot:
        for mid, post in bot_posts.items():
            title, desc = split_caption(post["text"])
            try:
                got = bot_download(post["full"]["file_id"],
                                   IMG_DIR / f"tg_{mid}_0")
                if not got:
                    continue
                full_path, is_new = got
                thumb_path = full_path
                if post["thumb"]:
                    t = bot_download(post["thumb"]["file_id"],
                                     IMG_DIR / f"tg_{mid}_0_thumb")
                    if t:
                        thumb_path, thumb_new = t
                        is_new = is_new or thumb_new
            except Exception as e:  # noqa: BLE001
                print(f"AVVISO: foto bot {mid} non scaricata: {e}",
                      file=sys.stderr)
                continue
            downloaded += int(is_new)
            upsert(mid, 0, title, desc, post["date"], full_path, thumb_path)

    # 4) Foto cancellate dal canale -> via dal repo, ma solo quando la
    #    fonte autorevole e' lo scraping pubblico e dentro la finestra di
    #    messaggi realmente coperta: gli item piu' vecchi restano conservati.
    if floor_id and not use_bot:
        for iid in list(items.keys()):
            if item_num_id(iid) >= floor_id and iid not in seen_ids:
                for key in ("image", "thumb"):
                    p = ROOT / items[iid].get(key, "")
                    if p.name.startswith("tg_") and p.is_file():
                        p.unlink()
                items.pop(iid, None)

    # 5) Ordine: piu' recenti prima; limite di galleria
    def order_key(it):
        parts = str(it["id"]).split("-")
        try:
            return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            return (0, 0)

    ordered = sorted(items.values(), key=order_key, reverse=True)[:MAX_PHOTOS]

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": source_title,
        "source_url": source_url,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(ordered),
        "items": ordered,
    }
    JSON_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 6) Confermiamo gli aggiornamenti al bot solo a fine giro: se c'e'
    #    stato un errore a meta', le foto restano nella coda del bot e
    #    vengono riprese all'esecuzione successiva.
    if TOKEN and last_update_id is not None:
        bot_call("getUpdates", offset=last_update_id + 1, timeout=0)

    print(
        f"Fatto: {len(ordered)} foto dal canale '{source_title}' "
        f"({downloaded} nuove) -> {JSON_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
