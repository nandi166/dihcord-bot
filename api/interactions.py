"""
Aternos Discord Bot - Vercel-kompatibilis verzió
=================================================

Ez a fájl a Discord "Interactions Endpoint" mintát követi (HTTP alapú
slash command-ok), NEM a régi gateway-alapú (Client.run()) modellt.
Ez teszi lehetővé, hogy a bot serverless környezetben (Vercel) fusson,
mivel minden kérésre csak egyszer fut le a kód, nem tart nyitva
folyamatos kapcsolatot.

Szükséges környezeti változók (Vercel projekt Settings > Environment Variables):
  DISCORD_PUBLIC_KEY      - Discord Developer Portal > General Information > Public Key
  ATERNOS_USERNAME        - Aternos fiók felhasználóneved
  ATERNOS_PASSWORD        - Aternos fiók jelszavad
  ATERNOS_SERVER_INDEX    - (opcionális, alapértelmezett 0) hányadik szervered a listában
  ATERNOS_SERVER_ADDRESS  - pl. "yourservername.aternos.me:12345" (a /server_status parancshoz)
"""

import os
import json
from flask import Flask, request, jsonify, abort

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

app = Flask(__name__)

PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")

# Discord interaction type / response type konstansok
PING = 1
APPLICATION_COMMAND = 2
PONG = 1
CHANNEL_MESSAGE_WITH_SOURCE = 4


def verify_signature(signature: str, timestamp: str, body: bytes) -> bool:
    """Ellenőrzi, hogy a kérés valóban a Discord-tól jött-e (Ed25519 aláírás)."""
    if not PUBLIC_KEY or not signature or not timestamp:
        return False
    try:
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False


def get_aternos_server():
    """Bejelentkezik az Aternos fiókba és visszaadja a kívánt szervert.

    Megjegyzés: mivel serverless környezetben nincs garantált, hogy a
    process élve marad kérések között, minden hívásnál újra be kell
    jelentkezni. Ez lassabb, mint az eredeti, folyamatosan futó bot,
    de ez a serverless modell ára.
    """
    from python_aternos import Client

    username = os.environ["ATERNOS_USERNAME"]
    password = os.environ["ATERNOS_PASSWORD"]
    index = int(os.environ.get("ATERNOS_SERVER_INDEX", "0"))

    aternos = Client(username, password=password)
    servers = aternos.servers
    return servers[index]


def get_server_status_text() -> str:
    """Lekérdezi a Minecraft szerver élő állapotát az mcstatus könyvtárral."""
    from mcstatus import JavaServer

    address = os.environ.get("ATERNOS_SERVER_ADDRESS")
    if not address:
        return "⚠️ Az ATERNOS_SERVER_ADDRESS környezeti változó nincs beállítva."

    try:
        server = JavaServer.lookup(address)
        status = server.status()
        players = status.players.online
        max_players = status.players.max
        return (
            f"✅ A szerver **ONLINE**! Játékosok: {players}/{max_players}\n"
            f"Csatlakozás: `{address}`"
        )
    except Exception:
        return "❌ A szerver jelenleg **OFFLINE** vagy nem elérhető (esetleg még bootol)."


@app.route("/api/interactions", methods=["POST"])
def interactions():
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    body = request.get_data()

    if not verify_signature(signature, timestamp, body):
        abort(401, "invalid request signature")

    data = request.get_json()

    # Discord "PING" - ezt küldi, amikor elmented az Interactions Endpoint URL-t
    if data.get("type") == PING:
        return jsonify({"type": PONG})

    if data.get("type") == APPLICATION_COMMAND:
        command_name = data["data"]["name"]
        member = data.get("member") or {}
        user = member.get("user") or data.get("user") or {}
        username = user.get("username", "ismeretlen felhasználó")

        if command_name == "hello":
            return jsonify(
                {
                    "type": CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {"content": f"Hello {username}! 👋"},
                }
            )

        if command_name == "server_status":
            return jsonify(
                {
                    "type": CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {"content": get_server_status_text()},
                }
            )

        if command_name == "server_start":
            try:
                server = get_aternos_server()
                server.start()
                content = (
                    "🚀 Szerverindítási parancs elküldve! Az Aternos ingyenes "
                    "sorban állás miatt ez 2-5 percig is eltarthat.\n"
                    "Ellenőrizd az `/server_status` paranccsal, hogy már fut-e!"
                )
            except Exception as exc:  # noqa: BLE001
                content = f"⚠️ Hiba történt a szerver indításakor: `{exc}`"

            return jsonify(
                {"type": CHANNEL_MESSAGE_WITH_SOURCE, "data": {"content": content}}
            )

        if command_name == "server_stop":
            try:
                server = get_aternos_server()
                server.stop()
                content = "🛑 Szerverleállítási parancs elküldve."
            except Exception as exc:  # noqa: BLE001
                content = f"⚠️ Hiba történt a szerver leállításakor: `{exc}`"

            return jsonify(
                {"type": CHANNEL_MESSAGE_WITH_SOURCE, "data": {"content": content}}
            )

        return jsonify(
            {
                "type": CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": f"Ismeretlen parancs: {command_name}"},
            }
        )

    return jsonify({"error": "unknown interaction type"}), 400


# Helyi teszteléshez: `python api/interactions.py`
if __name__ == "__main__":
    app.run(port=3000, debug=True)
