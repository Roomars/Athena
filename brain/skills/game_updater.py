"""
Skill: info e patch notes di giochi Steam via API pubblica (no API key).
Trigger: "patch notes di X", "ultime news di X", "aggiornamenti steam", "novità X steam".
"""
import re
import logging
from ._base import Skill

log = logging.getLogger("skill.game_updater")

_GAME_RE = re.compile(
    r'\b(?:patch\s+notes?|aggiornament[oi]\s+(?:di|per|steam)|novità\s+(?:di|per|su)|'
    r'ultime?\s+news\s+(?:di|su)|cosa\s+c\'è\s+di\s+nuovo|'
    r'update\s+(?:di|per)|nuova\s+versione\s+(?:di|per)|'
    r'changelog\s+(?:di|per))',
    re.I,
)

_GAME_NAME_RE = re.compile(
    r'\b(?:patch\s+notes?\s+(?:di|per)|aggiornament[oi]\s+(?:di|per)|novità\s+(?:di|per|su)|'
    r'ultime?\s+news\s+(?:di|su)|update\s+(?:di|per)|nuova\s+versione\s+(?:di|per)|'
    r'changelog\s+(?:di|per))\s+([A-Za-z0-9À-ÿ][A-Za-z0-9À-ÿ\s:\-\'\.]{1,40})',
    re.I,
)
# Suffissi da rimuovere dal nome gioco estratto
_GAME_SUFFIX_RE = re.compile(r'\s+(?:su|in|per)\s+(?:steam|yt|youtube)\s*$', re.I)

_STEAM_OPEN_RE = re.compile(
    r'\b(?:apri|avvia|lancia|gioca\s+a)\s+(.+?)\s+(?:su\s+)?steam\b',
    re.I,
)


class GameUpdaterSkill(Skill):
    name        = "game_updater"
    description = "Recupera patch notes e ultime news di giochi Steam via API pubblica."

    def match(self, text: str) -> dict | None:
        open_m = _STEAM_OPEN_RE.search(text)
        if open_m:
            return {"action": "open", "game": open_m.group(1).strip()}

        if not _GAME_RE.search(text):
            return None

        name_m = _GAME_NAME_RE.search(text)
        game = _GAME_SUFFIX_RE.sub("", name_m.group(1).strip()) if name_m else ""

        return {"action": "news", "game": game}

    async def run(self, _user_input: str, params: dict) -> str:
        import asyncio
        action = params.get("action", "news")
        game   = params.get("game", "")

        if action == "open":
            return await asyncio.get_event_loop().run_in_executor(
                None, _open_on_steam, game
            )
        return await asyncio.get_event_loop().run_in_executor(
            None, _get_news, game
        )


def _steam_search(game_name: str) -> tuple[int, str] | None:
    """Ritorna (app_id, titolo) per il primo risultato di ricerca Steam."""
    try:
        import httpx
        r = httpx.get(
            "https://store.steampowered.com/api/storesearch/",
            params={"term": game_name, "l": "italian", "cc": "IT"},
            timeout=8,
            headers={"User-Agent": "curl/7.88"},
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        if not items:
            return None
        first = items[0]
        return first["id"], first.get("name", game_name)
    except Exception as e:
        log.warning(f"steam search error: {e}")
        return None


def _get_news(game_name: str) -> str:
    if not game_name:
        return (
            "[GAME UPDATER] Specifica il gioco.\n"
            "Esempio: 'patch notes di Cyberpunk 2077' o 'ultime news di Elden Ring'"
        )

    result = _steam_search(game_name)
    if not result:
        return f"[GAME UPDATER] Gioco '{game_name}' non trovato su Steam."

    app_id, title = result

    try:
        import httpx
        r = httpx.get(
            "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/",
            params={"appid": app_id, "count": 3, "maxlength": 500, "format": "json"},
            timeout=8,
            headers={"User-Agent": "curl/7.88"},
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("appnews", {}).get("newsitems", [])
    except Exception as e:
        return f"[GAME UPDATER] Errore fetch news per '{title}': {e}"

    if not items:
        store_url = f"https://store.steampowered.com/app/{app_id}/"
        return (
            f"[GAME UPDATER: {title}]\n"
            f"Nessuna news recente trovata.\n"
            f"Store: {store_url}"
        )

    from datetime import datetime
    lines = [f"[GAME UPDATER: {title}] (App ID: {app_id})\n"]
    for item in items:
        ts    = item.get("date", 0)
        date  = datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else "?"
        title_n = item.get("title", "?")
        body  = item.get("contents", "").strip()
        # Pulisce tag BBCode / HTML basilari
        body  = re.sub(r'\[/?[a-z]+[^\]]*\]', '', body)
        body  = re.sub(r'<[^>]+>', '', body)
        body  = re.sub(r'\s{3,}', '\n', body).strip()
        if len(body) > 400:
            body = body[:400] + "..."
        lines.append(f"• {title_n} [{date}]\n  {body}")

    steam_url = f"steam://store/{app_id}"
    web_url   = f"https://store.steampowered.com/app/{app_id}/"
    lines.append(f"\nStore Steam: {web_url}")
    lines.append(f"Apri in Steam: {steam_url}")

    return "\n\n".join(lines)


def _open_on_steam(game_name: str) -> str:
    result = _steam_search(game_name)
    if not result:
        return f"[GAME UPDATER] Gioco '{game_name}' non trovato su Steam."

    app_id, title = result
    import subprocess
    try:
        subprocess.run(["open", f"steam://rungameid/{app_id}"], check=True)
        return f"[GAME UPDATER] Avvio '{title}' su Steam (App ID: {app_id})."
    except Exception as e:
        return f"[GAME UPDATER] Impossibile avviare '{title}': {e}"
