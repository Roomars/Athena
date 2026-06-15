import re
import subprocess

from ._base import Skill

_RE = re.compile(
    r"\b(?:apri|avvia|lancia|apri l[''']app|apri l[''']applicazione)\s+(.+)",
    re.I,
)

# Nomi italiani → nome esatto dell'app macOS (case-sensitive per `open -a`)
_ALIASES: dict[str, str] = {
    "calendario":     "Calendar",
    "foto":           "Photos",
    "mappe":          "Maps",
    "messaggi":       "Messages",
    "note":           "Notes",
    "promemoria":     "Reminders",
    "musica":         "Music",
    "notizie":        "News",
    "meteo":          "Weather",
    "calcolatrice":   "Calculator",
    "impostazioni":   "System Settings",
    "preferenze":     "System Settings",
    "posta":          "Mail",
    "contatti":       "Contacts",
    "facetime":       "FaceTime",
    "podcast":        "Podcasts",
    "libri":          "Books",
    "home":           "Home",
    "registratore":   "Voice Memos",
    "memo vocali":    "Voice Memos",
    "monitor attività": "Activity Monitor",
    "terminale":      "Terminal",
    "finder":         "Finder",
    "chrome":         "Google Chrome",
    "firefox":        "Firefox",
    "safari":         "Safari",
    "spotify":        "Spotify",
    "slack":          "Slack",
    "zoom":           "Zoom",
    "codice":         "Visual Studio Code",
    "vscode":         "Visual Studio Code",
    "xcode":          "Xcode",
}


def _resolve(raw: str) -> str:
    """Traduce il nome italiano nel nome app macOS, altrimenti lo usa così com'è."""
    key = raw.lower().strip()
    return _ALIASES.get(key, raw.strip())


class OpenAppSkill(Skill):
    name = "open_app"
    description = "Apre un'applicazione macOS tramite `open -a`."

    def match(self, text: str) -> dict | None:
        m = _RE.search(text)
        return {"app": m.group(1).strip()} if m else None

    async def run(self, _user_input: str, params: dict) -> str:
        raw = params["app"]
        app = _resolve(raw)
        r = subprocess.run(["open", "-a", app], capture_output=True, text=True)
        if r.returncode == 0:
            return f"[SKILL open_app] Ho aperto '{app}' con successo."
        else:
            return f"[SKILL open_app] Non riesco ad aprire '{app}': app non trovata sul sistema."
