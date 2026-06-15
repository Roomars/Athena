"""
Skill: controlla Safari via osascript.
Trigger: "apri X in safari", "vai su X", "naviga su X", "apri il sito X"
"""
import re
import subprocess
from ._base import Skill

_NAV_RE = re.compile(
    r'\b(?:vai\s+su|apri\s+(?:il\s+)?(?:sito|link|pagina|url)|'
    r'naviga\s+(?:su|a|verso)|apri\s+in\s+safari|'
    r'mostrami\s+(?:il\s+sito\s+)?(?:di\s+)?)\s*'
    r'(?P<target>(?:https?://)?[\w\-\.]+(?:\.[a-z]{2,})[^\s]*|[\w\s]+)',
    re.I,
)

_CLOSE_RE = re.compile(r'\bchiudi\s+(?:safari|il\s+browser|la\s+scheda)\b', re.I)
_RELOAD_RE = re.compile(r'\b(?:ricarica|aggiorna)\s+(?:la\s+)?pagina\b', re.I)
_URL_RE    = re.compile(r'https?://[^\s]+', re.I)


def _ensure_url(raw: str) -> str:
    raw = raw.strip().rstrip('.,?!')
    if raw.startswith('http'):
        return raw
    if '.' in raw and ' ' not in raw:
        return 'https://' + raw
    # Trattalo come query di ricerca
    from urllib.parse import quote_plus
    return f'https://duckduckgo.com/?q={quote_plus(raw)}'


class SafariControlSkill(Skill):
    name        = "safari_control"
    description = "Naviga in Safari tramite osascript: apri URL, cerca, ricarica, chiudi."

    def match(self, text: str) -> dict | None:
        # URL esplicito nel testo → priorità assoluta
        url_m = _URL_RE.search(text)
        if url_m and ('safari' in text.lower() or 'naviga' in text.lower()
                      or 'vai su' in text.lower() or 'apri' in text.lower()):
            return {"action": "navigate", "target": url_m.group(0)}
        if _CLOSE_RE.search(text):
            return {"action": "close"}
        if _RELOAD_RE.search(text):
            return {"action": "reload"}
        m = _NAV_RE.search(text)
        if m:
            return {"action": "navigate", "target": m.group("target").strip()}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, params
        )

    def _execute(self, params: dict) -> str:
        action = params["action"]

        def osascript(script: str) -> tuple[int, str]:
            r = subprocess.run(["osascript", "-e", script],
                               capture_output=True, text=True)
            return r.returncode, r.stderr.strip()

        if action == "navigate":
            url = _ensure_url(params["target"])
            script = f'''
tell application "Safari"
    activate
    if (count windows) = 0 then make new document
    set URL of current tab of front window to "{url}"
end tell'''
            code, err = osascript(script)
            if code == 0:
                return f"[SAFARI] Aperto: {url}"
            return f"[SAFARI] Errore: {err}"

        if action == "reload":
            code, err = osascript(
                'tell application "Safari" to do JavaScript '
                '"location.reload()" in current tab of front window'
            )
            return "[SAFARI] Pagina ricaricata." if code == 0 else f"[SAFARI] {err}"

        if action == "close":
            code, err = osascript(
                'tell application "Safari" to close front window'
            )
            return "[SAFARI] Safari chiuso." if code == 0 else f"[SAFARI] {err}"

        return "[SAFARI] Azione non riconosciuta."
