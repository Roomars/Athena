"""
HeartbeatMonitor — legge AI_Brain/HEARTBEAT.md ogni 15 minuti,
valuta i trigger attivi e notifica via Ari se il trigger scatta.

Spark system (ispirato a moeru-ai/airi): ogni notifica è un "spark"
persistito su SQLite via spark_store — cooldown e rate limit sopravvivono
al riavvio del daemon.

Trigger supportati (da HEARTBEAT.md):
  TRIGGER / CHECK / WINDOW / NOTIFY / CONTEXT
"""
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

from .spark_store import spark_store

log = logging.getLogger("heartbeat")

HEARTBEAT_PATH = Path(
    "/Users/roby/Library/CloudStorage/"
    "GoogleDrive-roberto.verzeletti.87@gmail.com/Il mio Drive/"
    "AI_Brain/HEARTBEAT.md"
)

_INTERVAL    = 15 * 60   # 15 minuti
_MAX_PER_DAY = 2
_QUIET_START = 22
_QUIET_END   = 7


def _parse_triggers(text: str) -> list[dict]:
    pattern = re.compile(
        r'TRIGGER:\s*(?P<id>[^\n]+)\n'
        r'CHECK:\s*(?P<check>[^\n]+)\n'
        r'WINDOW:\s*(?P<window>[^\n]+)\n'
        r'NOTIFY:\s*(?P<notify>[^\n]+)\n'
        r'CONTEXT:\s*(?P<context>[^\n]+)',
        re.MULTILINE,
    )
    return [
        {
            "id":      m.group("id").strip(),
            "check":   m.group("check").strip(),
            "window":  m.group("window").strip(),
            "notify":  m.group("notify").strip(),
            "context": m.group("context").strip(),
        }
        for m in pattern.finditer(text)
    ]


def _in_quiet_hours(now: datetime) -> bool:
    h = now.hour
    return h >= _QUIET_START or h < _QUIET_END


def _evaluate_trigger(t: dict, now: datetime) -> bool:
    window = t["window"].lower()
    hour   = now.hour
    wday   = now.weekday()

    if "07:00" in window and "09:00" in window:
        return wday < 5 and 7 <= hour < 9
    if "domenica" in window and "19:00" in window:
        return wday == 6 and 19 <= hour < 21
    if "venerdì" in window and "sabato" in window:
        return (wday == 4 and hour >= 18) or (wday == 5 and hour < 10)
    if "lunedì" in window and "08:30" in window:
        return wday == 0 and hour == 8
    if "ogni mattina" in window:
        return 9 <= hour < 10
    if "ogni" in window:
        return True
    return False


def _format_notify(notify_template: str, trigger_id: str, now: datetime) -> str:
    return (
        notify_template
        .replace("{{data}}", now.strftime("%d/%m/%Y"))
        .replace("{{ora}}", now.strftime("%H:%M"))
        .replace("{{titolo}}", trigger_id)
        .replace("{{N}}", "?")
    )


def _append_log(content: str, tid: str, notify: str, now: datetime) -> None:
    """Appende una riga al log table in HEARTBEAT.md."""
    log_line = f"| {now.strftime('%Y-%m-%d %H:%M')} | {tid} | {notify[:60]} |\n"
    if log_line in content:
        return
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if "nessuna ancora" in line or (i > 0 and "---|---|---" in lines[i - 1]):
            lines[i] = log_line
            break
    try:
        HEARTBEAT_PATH.write_text("".join(lines), encoding="utf-8")
    except Exception as e:
        log.warning(f"Heartbeat: impossibile aggiornare log — {e}")


async def heartbeat_loop(send_fn, tts=None) -> None:
    """Loop principale — scatta spark se un trigger è valido."""
    log.info("HeartbeatMonitor avviato — intervallo 15 min")

    while True:
        await asyncio.sleep(_INTERVAL)

        now = datetime.now()

        if _in_quiet_hours(now):
            continue

        try:
            content  = HEARTBEAT_PATH.read_text(encoding="utf-8")
            triggers = _parse_triggers(content)
        except Exception as e:
            log.warning(f"Heartbeat: impossibile leggere HEARTBEAT.md — {e}")
            continue

        # Rate limit globale: max _MAX_PER_DAY spark al giorno
        if spark_store.total_today() >= _MAX_PER_DAY:
            continue

        for t in triggers:
            tid = t["id"]

            # Cooldown 12h persistente via SQLite
            if not spark_store.cooldown_ok(tid, cooldown_hours=12):
                continue
            # Max 1 spark per trigger per giorno
            if spark_store.count_today(tid) >= 1:
                continue
            if not _evaluate_trigger(t, now):
                continue

            # Spark scattato
            notify = _format_notify(t["notify"], tid, now)
            title  = f"Ari · {tid}"
            log.info(f"Spark: {tid} → {notify}")

            await send_fn({
                "type":  "proactive_notification",
                "title": title,
                "body":  notify,
            })

            if tts:
                tts.speak(notify[:200])

            # Persisti su SQLite (cooldown e rate limit sopravvivono al riavvio)
            spark_store.record(tid, title, notify)

            # Log su HEARTBEAT.md
            _append_log(content, tid, notify, now)
