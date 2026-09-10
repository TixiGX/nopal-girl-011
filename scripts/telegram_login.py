#!/usr/bin/env python3
"""
Genera una volta sola la stringa di sessione Telegram (TG_SESSION) da salvare
nei secrets di GitHub. Serve un account Telegram membro del gruppo "Gallery".

    pip install -r scripts/requirements.txt
    python3 scripts/telegram_login.py

Ti chiederà API ID / API hash (da https://my.telegram.org/apps), numero di
telefono e il codice ricevuto su Telegram. Stampa la stringa: copiala nel
secret TG_SESSION. Non committarla mai nel repository.
"""
import getpass

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

api_id = int(input("API ID: ").strip())
api_hash = getpass.getpass("API hash: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\n=== TG_SESSION (copiala nei secrets, NON committarla) ===\n")
    print(client.session.save())
    print()
