import re
import subprocess
from datetime import datetime

from ._base import Skill

_WEEKDAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
_MONTHS   = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
              "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

_RE = re.compile(
    r"\b(?:che ore sono|che ora è|orario|ora attuale"
    r"|che giorno è|che data è|data di oggi"
    r"|batteria|carica batteria|livello batteria"
    r"|volume|luminosità)\b",
    re.I,
)


class SystemInfoSkill(Skill):
    name = "system_info"
    description = "Fornisce ora, data e stato della batteria."

    def match(self, text: str) -> dict | None:
        return {} if _RE.search(text) else None

    async def run(self, user_input: str, params: dict) -> str:
        now = datetime.now()
        day   = _WEEKDAYS[now.weekday()]
        month = _MONTHS[now.month - 1]
        parts = [
            f"Ora attuale: {now.strftime('%H:%M')}",
            f"Data: {day} {now.day} {month} {now.year}",
        ]

        try:
            out = subprocess.check_output(["pmset", "-g", "batt"], text=True)
            m = re.search(r"(\d+)%", out)
            if m:
                pct      = m.group(1)
                charging = "AC" in out and "discharging" not in out.lower()
                parts.append(f"Batteria: {pct}% {'(in carica)' if charging else '(non in carica)'}")
        except Exception:
            pass

        return "[SKILL system_info] " + " | ".join(parts)
