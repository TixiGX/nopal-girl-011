#!/usr/bin/env python3
"""
Sincronizza le foto del gruppo Telegram "Gallery" nella galleria del sito.

- Legge tutti i messaggi con foto del gruppo (link di invito o @username)
- Scarica le nuove foto in assets/images/telegram/<message_id>.jpg
- Rimuove le foto dei messaggi cancellati
- Scrive assets/data/gallery.json che il sito carica via fetch

Uso locale:
    pip install -r scripts/requirements.txt
    python3 scripts/telegram_login.py          # una volta sola: genera TG_SESSION
    TG_API_ID=... TG_API_HASH=... TG_SESSION=... python3 scripts/sync_telegram.py

Variabili d'ambiente:
    TG_API_ID, TG_API_HASH   da https://my.telegram.org/apps
    TG_SESSION               stringa di sessione (StringSession) di Telethon
    TG_CHAT                  link di invito o @username (default: gruppo Gallery)
    TG_MAX_PHOTOS            massimo di foto da tenere (default 200)
"""
import asyncio
import json
import os
import re
import sys
from datetime import timezone
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
    from telethon.tl.types import ChatInviteAlready, MessageMediaPhoto
    from telethon.errors import UserAlreadyParticipantError
except ImportError:
    sys.exit("Telethon non installato: pip install -r scripts/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "images" / "telegram"
JSON_PATH = ROOT / "assets" / "data" / "gallery.json"

API_ID = os.environ.get("TG_API_ID")
API_HASH = os.environ.get("TG_API_HASH")
SESSION = os.environ.get("TG_SESSION")
CHAT = os.environ.get("TG_CHAT", "https://t.me/+gjZgJrg2KqRkOWE0")
MAX_PHOTOS = int(os.environ.get("TG_MAX_PHOTOS", "200"))

INVITE_RE = re.compile(r"(?:t\.me/(?:\+|joinchat/)|^\+)([\w-]+)$")


def die(msg: str) -> None:
    print(f"ERRORE: {msg}", file=sys.stderr)
    sys.exit(1)


async def resolve_chat(client: TelegramClient):
    """Restituisce l'entità del gruppo, entrando via invito se necessario."""
    m = INVITE_RE.search(CHAT.strip())
    if not m:
        return await client.get_entity(CHAT)
    invite_hash = m.group(1)
    info = await client(CheckChatInviteRequest(invite_hash))
    if isinstance(info, ChatInviteAlready):
        return info.chat
    try:
        updates = await client(ImportChatInviteRequest(invite_hash))
        return updates.chats[0]
    except UserAlreadyParticipantError:
        info = await client(CheckChatInviteRequest(invite_hash))
        return info.chat


def split_caption(text: str):
    """Prima riga → titolo, resto → descrizione."""
    text = (text or "").strip()
    if not text:
        return "", ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0][:80]
    description = " ".join(lines[1:])[:240]
    return title, description


def photo_size(msg):
    """(width, height) della dimensione più grande della foto, se disponibile."""
    try:
        sizes = [s for s in msg.photo.sizes if hasattr(s, "w") and hasattr(s, "h")]
        best = max(sizes, key=lambda s: s.w * s.h)
        return best.w, best.h
    except Exception:
        return None, None


async def main() -> None:
    if not (API_ID and API_HASH and SESSION):
        die("Imposta TG_API_ID, TG_API_HASH e TG_SESSION (vedi scripts/telegram_login.py)")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with TelegramClient(StringSession(SESSION), int(API_ID), API_HASH) as client:
        chat = await resolve_chat(client)
        title = getattr(chat, "title", str(chat))
        print(f"Gruppo: {title}")

        items = []
        seen_files = set()
        downloaded = 0

        async for msg in client.iter_messages(chat, limit=None):
            if not msg.photo or not isinstance(msg.media, MessageMediaPhoto):
                continue
            fname = f"{msg.id}.jpg"
            fpath = IMG_DIR / fname
            if not fpath.exists():
                await client.download_media(msg, file=str(fpath))
                downloaded += 1
                print(f"  ↓ {fname}")
            seen_files.add(fname)

            w, h = photo_size(msg)
            t, d = split_caption(msg.message)
            items.append({
                "id": msg.id,
                "file": f"assets/images/telegram/{fname}",
                "title": t,
                "description": d,
                "date": msg.date.astimezone(timezone.utc).isoformat(timespec="seconds"),
                "width": w,
                "height": h,
            })
            if len(items) >= MAX_PHOTOS:
                break

        # Rimuove le foto non più presenti nel gruppo
        removed = 0
        for f in IMG_DIR.glob("*.jpg"):
            if f.name not in seen_files:
                f.unlink()
                removed += 1

        # Dal più recente al più vecchio
        items.sort(key=lambda x: x["id"], reverse=True)

        data = {
            "source": title,
            "updated": __import__("datetime").datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "count": len(items),
            "items": items,
        }
        JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Fatto: {len(items)} foto ({downloaded} nuove, {removed} rimosse) → {JSON_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
