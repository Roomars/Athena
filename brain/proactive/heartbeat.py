"""
HeartbeatMonitor — legge AI_Brain/HEARTBEAT.md ogni 15 minuti,
valuta i trigger attivi e notifica via Ari se il trigger scatta.

Trigger supportati (da HEARTBEAT.md):
  TRIGGER / CHECK / WINDOW / NOTIFY / CONTEXT
"""
import asyncio
import logging
import re
import time
from datetime import datetime
from pathlib import Path

log = logging.getLogger("heartbeat")

HEARTBEAT_PATH = Path(
    "/Users/roby/Library/CloudStorage/"
    "GoogleDrive-roberto.verzeletti.87@gmail.com/Il mio Drive/"
    "AI_Brain/HEARTBEAT.md"
)
VAULT_ROOT = HEARTBEAT_PATH.parent

_INTERVAL      = 15 * 60   # 15 minuti
_MAX_PER_DAY   = 2
_QUIET_START   = 22        # ora inizio silenzio
_QUIET_END     = 7         # ora fine silenzio

# State: trigger_id → ultimo_fire (timestamp)
_fired: dict[str, float] = {}
_day_count: dict[str, int] = {}
_last_day: str = ""


def _parse_triggers(text: str) -> list[dict]:
    """Estrae blocchi TRIGGER dal HEARTBEAT.md."""
    pattern = re.compile(
        r'TRIGGER:\s*(?P<id>[^\n]+)\n'
        r'CHECK:\s*(?P<check>[^\n]+)\n'
        r'WINDOW:\s*(?P<window>[^\n]+)\n'
        r'NOTIFY:\s*(?P<notify>[^\n]+)\n'
        r'CONTEXT:\s*(?P<context>[^\n]+)',
        re.MULTILINE,
    )
    triggers = []
    for m in pattern.finditer(text):
        triggers.append({
            "id":      m.group("id").strip(),
            "check":   m.group("check").strip(),
            "window":  m.group("window").strip(),
            "notify":  m.group("notify").strip(),
            "context": m.group("context").strip(),
        })
    return triggers


def _in_quiet_hours(now: datetime) -> bool:
    h = now.hour
    return h >= _QUIET_START or h < _QUIET_END


def _cooldown_ok(trigger_id: str, cooldown_hours: float = 24) -> bool:
    last = _fired.get(trigger_id, 0)
    return (time.monotonic() - last) >= cooldown_hours * 3600


def _evaluate_trigger(t: dict, now: datetime) -> bool:
    """Valuta se un trigger deve scattare in base alla WINDOW e all'ora attuale."""
    window = t["window"].lower()
    hour   = now.hour
    wday   = now.weekday()  # 0=Mon … 6=Sun

    # Feriali mattina 07:00-09:00
    if "07:00" in window and "09:00" in window:
        return wday < 5 and 7 <= hour < 9

    # Domenica 19:00-21:00
    if "domenica" in window and "19:00" in window:
        return wday == 6 and 19 <= hour < 21

    # Venerdì 18:00 – sabato 10:00
    if "venerdì" in window and "sabato" in window:
        return (wday == 4 and hour >= 18) or (wday == 5 and hour < 10)

    # Lunedì mattina 08:30
    if "lunedì" in window and "08:30" in window:
        return wday == 0 and hour == 8

    # Ogni mattina alle 09:00
    if "ogni mattina" in window:
        return 9 <= hour < 10

    # Ogni ora / finestra generica (notifica ogni 15min in window)
    if "ogni" in window:
        return True

    # X ore prima: non abbiamo il calendario integrato qui, skip per ora
    if "h" in window and any(c.isdigit() for c in window):
        return False

    # Finestre giorni (N giorni)
    if "giorni" in window or "days" in window:
        return False

    return False


def _format_notify(notify_template: str, trigger_id: str, now: datetime) -> str:
    return (
        notify_template
        .replace("{{data}}", now.strftime("%d/%m/%Y"))
        .replace("{{ora}}", now.strftime("%H:%M"))
        .replace("{{titolo}}", trigger_id)
        .replace("{{N}}", "?")
    )


async def heartbeat_loop(send_fn, tts=None) -> None:
    """Loop principale — chiama send_fn con payload notifica se un trigger scatta."""
    global _last_day, _day_count

    log.info("HeartbeatMonitor avviato — intervallo 15 min")

    while True:
        await asyncio.sleep(_INTERVAL)

        now     = datetime.now()
        day_key = now.strftime("%Y-%m-%d")

        # Reset contatore giornaliero
        if day_key != _last_day:
            _last_day  = day_key
            _day_count = {}

        if _in_quiet_hours(now):
            continue

        # Leggi HEARTBEAT.md
        try:
            content  = HEARTBEAT_PATH.read_text(encoding="utf-8")
            triggers = _parse_triggers(content)
        except Exception as e:
            log.warning(f"Heartbeat: impossibile leggere HEARTBEAT.md — {e}")
            continue

        total_today = sum(_day_count.values())
        if total_today >= _MAX_PER_DAY:
            continue

        for t in triggers:
            tid = t["id"]
            if not _cooldown_ok(tid, cooldown_hours=12):
                continue
            if _day_count.get(tid, 0) >= 1:
                continue
            if not _evaluate_trigger(t, now):
                continue

            # Trigger scattato
            notify = _format_notify(t["notify"], tid, now)
            log.info(f"Heartbeat trigger: {tid} → {notify}")

            await send_fn({
                "type":  "proactive_notification",
                "title": f"Heartbeat: {tid}",
                "body":  notify,
            })

            if tts:
                tts.speak(notify[:200])

            _fired[tid]     = time.monotonic()
            _day_count[tid] = _day_count.get(tid, 0) + 1

            # Appendi al log nel HEARTBEAT.md
            try:
                log_line = f"| {now.strftime('%Y-%m-%d %H:%M')} | {tid} | {notify} |\n"
                text_new = content.replace(
                    "| — | — | nessuna ancora |\n",
                    log_line,
                ).replace(
                    "nessuna ancora",
                    notify[:60],
                )
                # Append semplice in fondo alla tabella log
                if log_line not in content:
                    lines = content.splitlines(keepends=True)
                    for i, line in enumerate(lines):
                        if "nessuna ancora" in line or (i > 0 and "---|---|---" in lines[i-1]):
                            lines[i] = log_line
                            break
                    HEARTBEAT_PATH.write_text("".join(lines), encoding="utf-8")
            except Exception as e:
                log.warning(f"Heartbeat: impossibile aggiornare log — {e}")
