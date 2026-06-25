"""
Skill: invia messaggi via Messages.app tramite osascript (iMessage/SMS locale).
Trigger: "manda un messaggio a X: Y", "scrivi a X che Y", "messaggia X con Y"
Nessuna dipendenza esterna — solo osascript.
"""
import asyncio
import logging
import re
import subprocess
from ._base import Skill

log = logging.getLogger("skill.send_message")

# "manda/invia/scrivi messaggio a RECIPIENT: BODY"
_SEND_RE = re.compile(
    r'\b(?:manda|invia|scrivi|spedisci)\s+(?:un\s+)?(?:messaggio|msg|sms)?\s*a\s+'
    r'([+\w][\w\s.@+\-]{0,60}?)'
    r'(?:\s*:\s*|\s+(?:che|dicendo|scrivendo)\s+(?:gli?\s+|le\s+)?(?:dico\s+|dici\s+)?|\s+con\s+(?:il\s+(?:messaggio|testo)\s*:\s*)?)'
    r'(.+)',
    re.I | re.S,
)

# "messaggia RECIPIENT e digli Y"
_MSGGIA_RE = re.compile(
    r'\bmessaggia\s+([+\w][\w\s.@+\-]{0,60}?)\s+(?:e\s+)?(?:di\w*\s+)?(.+)',
    re.I | re.S,
)


class SendMessageSkill(Skill):
    name        = "send_message"
    description = "Invia messaggi via Messages.app (iMessage/SMS)."

    def match(self, text: str) -> dict | None:
        for pattern in (_SEND_RE, _MSGGIA_RE):
            m = pattern.search(text)
            if m:
                recipient = m.group(1).strip().rstrip(",.")
                body      = m.group(2).strip().strip('"\'')
                if recipient and body:
                    return {"recipient": recipient, "body": body}
        return None

    async def run(self, _user_input: str, params: dict) -> str:
        recipient = params["recipient"]
        body      = params["body"]
        loop      = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _send, recipient, body)


def _send(recipient: str, body: str) -> str:
    # Sanifica: rimuovi virgolette interne per non rompere l'AppleScript
    safe_body      = body.replace('"', '\\"').replace('\\n', '\n')
    safe_recipient = recipient.replace('"', '')

    script = f'''
tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy "{safe_recipient}" of targetService
    send "{safe_body}" to targetBuddy
end tell
'''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            log.info(f"Messaggio inviato a {recipient!r}")
            return f"[MESSAGGIO INVIATO]\nA: {recipient}\nTesto: {body}"
        else:
            err = result.stderr.strip()
            log.warning(f"Errore osascript send_message: {err}")
            # Fallback: prova con phone/email direttamente (senza lookup buddy)
            return _send_fallback(safe_recipient, safe_body, err)
    except subprocess.TimeoutExpired:
        return "Timeout: Messages.app non ha risposto entro 10 secondi."
    except Exception as e:
        return f"Errore invio messaggio: {e}"


def _send_fallback(recipient: str, body: str, original_err: str) -> str:
    """Prova con 'send to participant' invece di 'buddy'."""
    script = f'''
tell application "Messages"
    send "{body}" to participant "{recipient}" of 1st account
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return f"[MESSAGGIO INVIATO]\nA: {recipient}\nTesto: {body}"
        else:
            return (
                f"Non riesco a trovare '{recipient}' in Messages.\n"
                f"Usa il numero di telefono o l'email iCloud.\n"
                f"Errore: {result.stderr.strip() or original_err}"
            )
    except Exception as e:
        return f"Errore invio messaggio (fallback): {e}"
