# Aternos Discord Bot – Vercel verzió

Ez a verzió **nem** az eredeti, folyamatosan futó (`discord.py` gateway alapú)
botot használja, hanem a Discord **Slash Command Interactions** rendszerét –
ez HTTP-kérés/válasz alapú, ezért fér csak bele a Vercel serverless
futtatókörnyezetébe.

**Ami emiatt más, mint az eredeti botnál:**
- Nincs `?server_start` szöveges parancs, helyette `/server_start` slash parancs.
- Nincs "várunk amíg online lesz, aztán szólunk" viselkedés (ez percekig tartana,
  a serverless function pedig max ~30 másodpercig futhat). Helyette:
  `/server_start` elindítja a szervert és azonnal válaszol, `/server_status`-szal
  pedig bármikor le tudod kérdezni, hogy már fut-e.

## 1. Discord alkalmazás létrehozása

1. Menj a [Discord Developer Portalra](https://discord.com/developers/applications)
2. **New Application** → adj neki nevet
3. A **Bot** fülön hozz létre egy bot usert, másold ki a **Token**-t
4. A **General Information** fülön másold ki az **Application ID**-t és a
   **Public Key**-t
5. A bot meghívásához (OAuth2 → URL Generator): scope = `applications.commands`,
   majd az így generált linkkel hívd meg a szerveredre

## 2. Környezeti változók beállítása Vercel-en

A Vercel projekt **Settings → Environment Variables** alatt add hozzá:

| Változó | Érték |
|---|---|
| `DISCORD_PUBLIC_KEY` | a Developer Portalból másolt Public Key |
| `ATERNOS_USERNAME` | az Aternos fiókod felhasználóneve |
| `ATERNOS_PASSWORD` | az Aternos fiókod jelszava |
| `ATERNOS_SERVER_ADDRESS` | pl. `yourservername.aternos.me:12345` |
| `ATERNOS_SERVER_INDEX` | opcionális, alapértelmezett `0` |

## 3. Deploy Vercel-re

Ha a repódat (ezt a fork-ot) importálod a [vercel.com](https://vercel.com) oldalon
"Add New Project" → GitHub repo kiválasztása módon, a Vercel automatikusan
felismeri a `requirements.txt`-t és Python function-ként telepíti az
`api/interactions.py`-t a következő URL-en:

```
https://<a-te-projekted>.vercel.app/api/interactions
```

## 4. Interactions Endpoint URL beállítása

A Discord Developer Portal → **General Information** oldalon van egy mező:
**"Interactions Endpoint URL"**. Ide illeszd be a fenti URL-t, majd mentsd el.

⚠️ Fontos: a Discord ekkor azonnal egy `PING` kérést küld erre a címre, és csak
akkor engedi elmenteni, ha helyes választ kap. Ehhez a Vercel deploy-nak és a
`DISCORD_PUBLIC_KEY` env változónak már élesben kell lennie – tehát **előbb
deployolj, utána állítsd be ezt a mezőt.**

## 5. Slash parancsok regisztrálása

Ezt egyszer, lokálisan kell lefuttatnod (nem a Vercel csinálja):

```bash
pip install requests
export DISCORD_APPLICATION_ID="ide-az-application-id"
export DISCORD_BOT_TOKEN="ide-a-bot-token"
python register_commands.py
```

Ha minden `[OK]`-t ír ki, a `/hello`, `/server_start`, `/server_stop`,
`/server_status` parancsok pár percen belül megjelennek a szerveren.

## 6. Tesztelés

Discord szerveren írd be: `/server_status` – ha helyes választ kapsz, minden
jól van beállítva.

## Korlátok, amikről tudnod kell

- **Az Aternos gyakran CAPTCHA-val védi a bejelentkezést.** Ha a
  `Client(username, password=...)` bejelentkezés elkezd hibázni, az Aternos
  valószínűleg bot-gyanús viselkedésnek érzékeli a serverless IP-ket
  (a Vercel megosztott IP-kről fut). Ez sajnos ismert korlátja a nem hivatalos
  Aternos API-knak, függetlenül a hosztelési platformtól.
- Minden `/server_start`/`/server_stop` hívásnál **újra bejelentkezik** az
  Aternos fiókba (mert serverless környezetben nincs garantáltan megőrzött
  állapot két kérés között) – ez lassabb, mint az eredeti, folyamatosan
  bejelentkezve maradó botnál volt.
- Ha az Aternos bejelentkezés rendszeresen elbukik, egy 24/7-es hosztelés
  (pl. Railway, Render Background Worker, saját VPS) az eredeti, változtatás
  nélküli kóddal megbízhatóbb megoldás lenne.
