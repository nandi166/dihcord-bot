"""
Egyszeri szkript a slash parancsok regisztrálásához.

Ezt NEM a Vercel futtatja - ezt te futtatod le LOKÁLISAN, egyszer,
miután létrehoztad a Discord alkalmazást. Utána a parancsok globálisan
elérhetők lesznek a szerveren (~1 órán belül frissülnek, ha épp
módosítod őket, de első regisztrációkor általában gyorsabb).

Használat:
  1. pip install requests
  2. Állítsd be a környezeti változókat (vagy írd be közvetlenül ide, majd töröld):
       export DISCORD_APPLICATION_ID="..."
       export DISCORD_BOT_TOKEN="..."
  3. python register_commands.py
"""

import os
import requests

APPLICATION_ID = os.environ["DISCORD_APPLICATION_ID"]
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

URL = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/commands"

HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
}

COMMANDS = [
    {
        "name": "hello",
        "description": "Üdvözlő üzenet a bottól",
        "type": 1,
    },
    {
        "name": "server_start",
        "description": "Elindítja az Aternos Minecraft szervert",
        "type": 1,
    },
    {
        "name": "server_stop",
        "description": "Leállítja az Aternos Minecraft szervert",
        "type": 1,
    },
    {
        "name": "server_status",
        "description": "Lekérdezi a szerver aktuális állapotát (online/offline, játékosok)",
        "type": 1,
    },
]

if __name__ == "__main__":
    for command in COMMANDS:
        resp = requests.post(URL, headers=HEADERS, json=command, timeout=10)
        status = "OK" if resp.status_code in (200, 201) else "HIBA"
        print(f"[{status}] /{command['name']} -> {resp.status_code}: {resp.text}")
