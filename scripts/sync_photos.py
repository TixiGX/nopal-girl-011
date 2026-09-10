#!/usr/bin/env python3
"""
Legge l'album condiviso di Google Foto e scrive l'elenco delle foto in
assets/data/photos.json, che il sito mostra direttamente nella galleria.

- Non scarica le foto: il sito le carica dagli URL diretti di Google,
  quindi la galleria è sempre sincronizzata senza appesantire il repository
- Il link dell'album NON è scritto qui dentro: va passato via variabile
  d'ambiente (su GitHub: secret PHOTOS_ALBUM_URL), così resta nascosto

Uso locale:
    PHOTOS_ALBUM_URL='https://photos.app.goo.gl/...' python3 scripts/sync_photos.py

Variabili d'ambiente:
    PHOTOS_ALBUM_URL   link di condivisione dell'album (obbligatorio)
    PHOTOS_MAX         massimo di foto da tenere (default 100)

Solo libreria standard: nessuna dipendenza da installare.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "assets" / "data" / "photos.json"

ALBUM_URL = os.environ.get("PHOTOS_ALBUM_URL", "").strip()
MAX_PHOTOS = int(os.environ.get("PHOTOS_MAX", "100"))

UA = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def die(msg: str) -> None:
    print(f"ERRORE: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def album_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if not m:
        return ""
    return unescape(m.group(1)).replace(" - Google Photos", "").strip()


def extract_bases(html: str):
    """URL base delle foto (senza parametri di dimensione), senza doppioni."""
    # Google codifica alcuni caratteri come \u003d (=): normalizza
    text = html.replace("\\u003d", "=").replace("\\u0026", "&")
    found = re.findall(
        r"https://lh3\.googleusercontent\.com/[A-Za-z0-9_\-\/\.]+(?:=[A-Za-z0-9_\-]+)?",
        text,
    )
    bases = []
    seen = set()
    for u in found:
        base = u.split("=")[0].rstrip("/")
        low = u.lower()
        # Scarta avatar e anteprime microscopiche dell'interfaccia
        if "/a/" in base or "/a-" in base:
            continue
        m = re.search(r"=s(\d+)", low)
        if m and int(m.group(1)) < 200:
            continue
        if base in seen:
            continue
        seen.add(base)
        bases.append(base)
    return bases


def main() -> None:
    if not ALBUM_URL:
        die("imposta PHOTOS_ALBUM_URL con il link di condivisione dell'album")
    try:
        html = fetch(ALBUM_URL)
    except Exception as e:  # noqa: BLE001 - mostra l'errore e fallisce il workflow
        die(f"impossibile leggere l'album: {e}")

    title = album_title(html) or "Album Google Foto"
    bases = extract_bases(html)[:MAX_PHOTOS]

    items = [
        {
            "id": i + 1,
            "image": f"{b}=w1600",
            "thumb": f"{b}=w600",
            "title": "",
            "description": "",
        }
        for i, b in enumerate(bases)
    ]

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "source": title,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(items),
        "items": items,
    }
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Fatto: {len(items)} foto dall'album '{title}' "
          f"-> {JSON_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
