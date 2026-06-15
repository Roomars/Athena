import re
import subprocess

from ._base import Skill

_RE_READ = re.compile(
    r"\b(?:leggi(?:\s+gli)?\s+appunti|cosa c[''']è negli appunti|appunti|clipboard|cosa ho copiato)\b",
    re.I,
)


class ClipboardSkill(Skill):
    name = "clipboard"
    description = "Legge il contenuto degli appunti (clipboard) di macOS."

    def match(self, text: str) -> dict | None:
        return {} if _RE_READ.search(text) else None

    async def run(self, user_input: str, params: dict) -> str:
        try:
            content = subprocess.check_output(["pbpaste"], text=True).strip()
            if content:
                preview = content[:800] + ("…" if len(content) > 800 else "")
                return f"[SKILL clipboard] Contenuto appunti: {preview}"
            return "[SKILL clipboard] Gli appunti sono vuoti."
        except Exception as e:
            return f"[SKILL clipboard] Errore lettura appunti: {e}"
