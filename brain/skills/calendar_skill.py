"""
Skill: leggi e scrivi Apple Calendar via osascript.
Trigger: cosa ho oggi/questa settimana, aggiungi evento, prossimo allenamento, partita.
"""
import re
import subprocess
from datetime import datetime, timedelta
from ._base import Skill

_READ_RE = re.compile(
    r'\b(?:'
    r'cosa\s+ho\s+(?:oggi|domani|questa\s+settimana|lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica)'
    r'|agenda\s+(?:di\s+)?(?:oggi|domani|settimana)'
    r'|eventi\s+(?:di\s+)?(?:oggi|domani|questa\s+settimana)'
    r'|calendario\s+(?:di\s+)?(?:oggi|domani)'
    r'|impegni\s+(?:di\s+)?(?:oggi|domani|settimana)'
    r'|prossim[oa]\s+(?:allenamento|partita|riunione|evento|appuntamento)'
    r'|ho\s+qualcosa\s+(?:oggi|domani)'
    r')',
    re.I,
)
_ADD_RE = re.compile(
    r'\b(?:aggiungi|crea|metti|segna|inserisci)\s+'
    r'(?:un\s+)?(?:evento|appuntamento|riunione|allenamento|partita)\b',
    re.I,
)
_WEEK_RE = re.compile(r'\bsettimana\b', re.I)
_TOMORROW_RE = re.compile(r'\bdomani\b', re.I)


def _osascript(script: str) -> str:
    r = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10,
    )
    return r.stdout.strip() if r.returncode == 0 else f"Errore: {r.stderr.strip()}"


def _get_events(date_str: str, end_date_str: str | None = None) -> str:
    """Legge eventi da Calendar.app per l'intervallo dato (formato YYYY-MM-DD)."""
    end = end_date_str or date_str
    script = f"""
set startDate to date "{date_str}"
set endDate to date "{end} 23:59:59"
set output to ""
tell application "Calendar"
    repeat with aCal in every calendar
        set evts to (every event of aCal whose start date >= startDate and start date <= endDate)
        repeat with e in evts
            set t to start date of e
            set h to hours of t
            set m to minutes of t
            set mStr to text -2 thru -1 of ("0" & m)
            set hStr to text -2 thru -1 of ("0" & h)
            set output to output & "• " & summary of e & " — " & hStr & ":" & mStr & " (" & name of aCal & ")" & linefeed
        end repeat
    end repeat
end tell
if output is "" then return "Nessun evento trovato."
return output
"""
    return _osascript(script)


def _add_event(title: str, date_str: str, hour: int = 10, duration_min: int = 60) -> str:
    end_hour = hour + duration_min // 60
    script = f"""
set startDate to date "{date_str} {hour:02d}:00:00"
set endDate to date "{date_str} {end_hour:02d}:00:00"
tell application "Calendar"
    tell calendar "Calendario"
        make new event with properties {{summary:"{title}", start date:startDate, end date:endDate}}
    end tell
end tell
return "ok"
"""
    r = _osascript(script)
    return r


class CalendarSkill(Skill):
    name        = "calendar"
    description = "Leggi e scrivi eventi in Apple Calendar via osascript."

    def match(self, text: str) -> dict | None:
        if _ADD_RE.search(text):
            return {"action": "add", "raw": text}
        if _READ_RE.search(text):
            if _WEEK_RE.search(text):
                return {"action": "week"}
            if _TOMORROW_RE.search(text):
                return {"action": "tomorrow"}
            return {"action": "today"}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, params
        )

    def _execute(self, params: dict) -> str:
        action = params.get("action")
        today = datetime.now()

        if action == "today":
            events = _get_events(today.strftime("%Y-%m-%d"))
            return f"[CALENDAR] Agenda di oggi ({today.strftime('%d/%m/%Y')}):\n{events}"

        if action == "tomorrow":
            tom = today + timedelta(days=1)
            events = _get_events(tom.strftime("%Y-%m-%d"))
            return f"[CALENDAR] Agenda di domani ({tom.strftime('%d/%m/%Y')}):\n{events}"

        if action == "week":
            end = today + timedelta(days=7)
            events = _get_events(today.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            return f"[CALENDAR] Prossimi 7 giorni:\n{events}"

        if action == "add":
            # Parsing base: estrai titolo e data dal testo grezzo
            raw = params.get("raw", "")
            title = re.sub(_ADD_RE, "", raw).strip().rstrip(".,!?") or "Evento"
            # Data: cerca "domani", "lunedì", o data esplicita — default: domani
            date_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            r = _add_event(title, date_str)
            if "ok" in r:
                return f"[CALENDAR] Evento «{title}» aggiunto per {date_str}."
            return f"[CALENDAR] Errore creazione evento: {r}"

        return "[CALENDAR] Azione non riconosciuta."
