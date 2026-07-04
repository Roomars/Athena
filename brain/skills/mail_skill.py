"""
Skill: leggi Mail.app via osascript.
Trigger: email non lette, cerca email da X, ultima email di X, quante email ho.
"""
import re
import subprocess
from ._base import Skill

_UNREAD_RE = re.compile(
    r'\b(?:'
    r'email\s+(?:non\s+)?(?:lette|letta|nuove|in\s+arrivo)'
    r'|quante\s+(?:email|mail)\s+ho'
    r'|ho\s+(?:email|mail|posta)\b'
    r'|posta\s+(?:in\s+arrivo|non\s+letta)'
    r'|messaggi\s+non\s+letti'
    r'|controlla\s+(?:la\s+)?(?:posta|mail|email)'
    r')',
    re.I,
)
_SEARCH_RE = re.compile(
    r'\b(?:cerca|trova|hai\s+ricevuto|ho\s+ricevuto)\s+'
    r'(?:una\s+)?(?:email|mail)?\s*(?:da|di|su|riguardo)\s+'
    r'(?P<query>.+)',
    re.I,
)
_FROM_RE = re.compile(
    r'\b(?:email|mail|posta)\s+da\s+(?P<sender>.+)',
    re.I,
)


def _osascript(script: str) -> str:
    r = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=15,
    )
    return r.stdout.strip() if r.returncode == 0 else f"Errore: {r.stderr.strip()}"


def _unread_count() -> str:
    script = """
tell application "Mail"
    set cnt to count of (messages of inbox whose read status is false)
    return cnt as string
end tell
"""
    return _osascript(script)


def _get_unread(max_count: int = 5) -> str:
    script = f"""
tell application "Mail"
    set msgs to (messages of inbox whose read status is false)
    set output to ""
    set n to count of msgs
    if n = 0 then return "Nessuna email non letta."
    repeat with i from 1 to (minimum value of {{n, {max_count}}})
        set m to item i of msgs
        set output to output & "• Da: " & (sender of m) & linefeed
        set output to output & "  Oggetto: " & (subject of m) & linefeed
        set output to output & "  Data: " & ((date received of m) as string) & linefeed & linefeed
    end repeat
    if n > {max_count} then set output to output & "...e altre " & (n - {max_count}) & " email." & linefeed
    return output
end tell
"""
    return _osascript(script)


def _search_by_subject(query: str, max_count: int = 5) -> str:
    safe = query.replace('"', '\\"')[:60]
    script = f"""
tell application "Mail"
    set msgs to (messages of inbox whose subject contains "{safe}")
    set output to ""
    set n to count of msgs
    if n = 0 then return "Nessuna email trovata su: {safe}"
    repeat with i from 1 to (minimum value of {{n, {max_count}}})
        set m to item i of msgs
        set output to output & "• Da: " & (sender of m) & " — " & (subject of m) & " (" & ((date received of m) as string) & ")" & linefeed
    end repeat
    return output
end tell
"""
    return _osascript(script)


class MailSkill(Skill):
    name        = "mail"
    description = "Leggi email non lette o cerca in Mail.app via osascript."

    def match(self, text: str) -> dict | None:
        m = _SEARCH_RE.search(text)
        if m:
            return {"action": "search", "query": m.group("query").strip().rstrip("?.,!")}
        m = _FROM_RE.search(text)
        if m:
            return {"action": "search", "query": m.group("sender").strip().rstrip("?.,!")}
        if _UNREAD_RE.search(text):
            return {"action": "unread"}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, params
        )

    def _execute(self, params: dict) -> str:
        action = params.get("action")

        if action == "unread":
            count = _unread_count()
            if count == "0":
                return "[MAIL] Inbox zero — nessuna email non letta."
            details = _get_unread()
            return f"[MAIL] {count} email non lette:\n{details}"

        if action == "search":
            query   = params.get("query", "")
            results = _search_by_subject(query)
            return f"[MAIL] Ricerca «{query}»:\n{results}"

        return "[MAIL] Azione non riconosciuta."
