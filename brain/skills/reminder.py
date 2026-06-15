"""
Skill: crea promemoria in Reminders.app via osascript.
Trigger: "ricordami di X", "crea un promemoria per X", "memo X", "aggiungi promemoria X"
"""
import re
import subprocess
from ._base import Skill

_RE = re.compile(
    r'\b(?:'
    r'ricordami\s+(?:di\s+|che\s+)?'
    r'|crea\s+(?:un\s+)?promemoria\s+(?:per\s+|di\s+)?'
    r'|aggiungi\s+(?:un\s+)?promemoria\s+(?:per\s+|di\s+)?'
    r'|metti\s+(?:un\s+)?promemoria\s+(?:per\s+|di\s+)?'
    r'|memo\s+'
    r'|imposta\s+(?:un\s+)?reminder\s+(?:per\s+)?'
    r')(?P<task>.+)',
    re.I,
)


class ReminderSkill(Skill):
    name        = "reminder"
    description = "Crea promemoria in Reminders.app tramite osascript."

    def match(self, text: str) -> dict | None:
        m = _RE.search(text)
        if not m:
            return None
        task = m.group("task").strip().rstrip('.,?!')
        return {"task": task}

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._create, params["task"]
        )

    def _create(self, task: str) -> str:
        safe = task.replace('\\', '\\\\').replace('"', '\\"')
        script = f'tell application "Reminders" to make new reminder with properties {{name:"{safe}"}}'
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if r.returncode == 0:
            return f"[REMINDER] Promemoria creato: «{task}»"
        return f"[REMINDER] Errore: {r.stderr.strip() or 'permesso negato a Reminders.app'}"
