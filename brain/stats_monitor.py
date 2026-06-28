"""
Raccoglie metriche di sistema ogni 2s e le invia via WebSocket.
Metriche: CPU %, Memoria, Disco I/O, Rete ↓↑, Temperatura (best-effort), Disco usato %.
Anomalie: rileva soglie critiche e notifica Ari via TTS + response panel.
"""
import asyncio
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import psutil

_INTERVAL = 2.0


# ── Formato ──────────────────────────────────────────────────────────────────

def _fmt_bytes(b: float) -> str:
    if b < 1_024:
        return f"{b:.0f} B/s"
    if b < 1_048_576:
        return f"{b / 1_024:.1f} KB/s"
    return f"{b / 1_048_576:.1f} MB/s"


def _temperature() -> float | None:
    try:
        out = subprocess.check_output(
            ["osx-cpu-temp"], text=True, timeout=1, stderr=subprocess.DEVNULL
        )
        import re
        m = re.search(r"([\d.]+)", out)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None


# ── Rilevamento anomalie ──────────────────────────────────────────────────────

@dataclass
class _Rule:
    key:         str          # chiave nel payload stats
    threshold:   float        # valore oltre cui è anomalia
    cooldown:    float        # secondi minimi tra due alert dello stesso tipo
    consecutive: int          # check consecutivi richiesti prima di scattare
    title:       str
    body_fn: Callable[[float], str]
    _count:      int   = field(default=0, init=False)
    _last_fired: float = field(default=0.0, init=False)

    def evaluate(self, value: float | None) -> tuple[str, str] | None:
        """Ritorna (title, body) se l'anomalia scatta, altrimenti None."""
        if value is None:
            self._count = 0
            return None

        now = time.monotonic()
        if value > self.threshold:
            self._count += 1
            if self._count >= self.consecutive and (now - self._last_fired) >= self.cooldown:
                self._last_fired = now
                self._count = 0
                return self.title, self.body_fn(value)
        else:
            self._count = 0
        return None


_RULES: list[_Rule] = [
    _Rule(
        key="cpu_pct", threshold=85, cooldown=600, consecutive=3,
        title="CPU sotto sforzo",
        body_fn=lambda v: f"CPU al {v:.0f}% da diversi secondi. Qualcosa sta lavorando intensamente.",
    ),
    _Rule(
        key="mem_pct", threshold=88, cooldown=900, consecutive=2,
        title="Memoria quasi esaurita",
        body_fn=lambda v: f"RAM all'{v:.0f}%. Considera di chiudere qualche applicazione.",
    ),
    _Rule(
        key="disk_used_pct", threshold=90, cooldown=3600, consecutive=1,
        title="Disco quasi pieno",
        body_fn=lambda v: f"Il disco principale è al {v:.0f}%. Fai un po' di spazio.",
    ),
    _Rule(
        key="temp_c", threshold=85, cooldown=300, consecutive=2,
        title="Temperatura elevata",
        body_fn=lambda v: f"CPU a {v:.0f}°C. Controlla se c'è qualcosa che la stessa scalda.",
    ),
]


class AnomalyDetector:
    def __init__(self):
        self._rules = _RULES

    def check(self, payload: dict) -> list[tuple[str, str]]:
        """Ritorna lista di (title, body) per le anomalie scattate in questo tick."""
        alerts = []
        for rule in self._rules:
            value = payload.get(rule.key)
            # disk_used_pct e temp_c sono già numerici; cpu_pct e mem_pct idem
            if isinstance(value, str):
                continue
            result = rule.evaluate(value)
            if result:
                alerts.append(result)
        return alerts


# ── Loop principale ───────────────────────────────────────────────────────────

async def stats_loop(send_fn) -> None:
    """Loop principale — send_fn è manager.send dal ws_handler."""
    from .tts import tts  # import locale per evitare circolarità al boot

    psutil.cpu_percent(interval=None)   # prima lettura: scarta il delta
    prev_net  = psutil.net_io_counters()
    prev_disk = psutil.disk_io_counters()   # può essere None su VM
    prev_ts   = time.monotonic()
    detector  = AnomalyDetector()

    while True:
        await asyncio.sleep(_INTERVAL)

        now    = time.monotonic()
        dt     = max(now - prev_ts, 0.001)
        prev_ts = now

        cpu_pct = psutil.cpu_percent(interval=None)

        mem       = psutil.virtual_memory()
        mem_used  = mem.used  / 1_073_741_824
        mem_total = mem.total / 1_073_741_824
        mem_pct   = mem.percent

        disk_io    = psutil.disk_io_counters()
        if disk_io is not None and prev_disk is not None:
            disk_read  = (disk_io.read_bytes  - prev_disk.read_bytes)  / dt
            disk_write = (disk_io.write_bytes - prev_disk.write_bytes) / dt
            prev_disk  = disk_io
        else:
            disk_read = disk_write = 0.0

        disk_used_pct = psutil.disk_usage("/").percent

        net      = psutil.net_io_counters()
        net_down = (net.bytes_recv - prev_net.bytes_recv) / dt
        net_up   = (net.bytes_sent - prev_net.bytes_sent) / dt
        prev_net = net

        temp = _temperature()

        payload = {
            "type":          "stats_update",
            "cpu_pct":       round(cpu_pct, 1),
            "mem_used_gb":   round(mem_used, 1),
            "mem_total_gb":  round(mem_total, 1),
            "mem_pct":       round(mem_pct, 1),
            "disk_read":     _fmt_bytes(disk_read),
            "disk_write":    _fmt_bytes(disk_write),
            "disk_used_pct": round(disk_used_pct, 1),
            "net_down":      _fmt_bytes(net_down),
            "net_up":        _fmt_bytes(net_up),
            "temp_c":        round(temp, 1) if temp is not None else None,
        }

        await send_fn(payload)

        # Anomalie — controlla e notifica
        for title, body in detector.check(payload):
            await send_fn({
                "type":  "proactive_notification",
                "title": title,
                "body":  body,
            })
            tts.speak(f"{title}. {body}")
