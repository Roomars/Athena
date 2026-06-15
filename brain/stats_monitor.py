"""
Raccoglie metriche di sistema ogni 2s e le invia via WebSocket.
Metriche: CPU %, Memoria, Disco I/O, Rete ↓↑, Temperatura (best-effort), Disco usato %.
"""
import asyncio
import subprocess
import time

import psutil

_INTERVAL = 2.0


def _fmt_bytes(b: float) -> str:
    """Converte byte/s in stringa leggibile."""
    if b < 1_024:
        return f"{b:.0f} B/s"
    if b < 1_048_576:
        return f"{b/1_024:.1f} KB/s"
    return f"{b/1_048_576:.1f} MB/s"


def _temperature() -> float | None:
    """Tenta di leggere la temperatura CPU via osx-cpu-temp (se installato)."""
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


async def stats_loop(send_fn) -> None:
    """Loop principale — send_fn è manager.send dal ws_handler."""
    # Prima lettura: scarta il delta iniziale
    psutil.cpu_percent(interval=None)
    prev_net  = psutil.net_io_counters()
    prev_disk = psutil.disk_io_counters()
    prev_ts   = time.monotonic()

    while True:
        await asyncio.sleep(_INTERVAL)

        now = time.monotonic()
        dt  = max(now - prev_ts, 0.001)
        prev_ts = now

        # CPU
        cpu_pct = psutil.cpu_percent(interval=None)

        # Memoria
        mem        = psutil.virtual_memory()
        mem_used   = mem.used   / 1_073_741_824   # GiB
        mem_total  = mem.total  / 1_073_741_824
        mem_pct    = mem.percent

        # Disco I/O
        disk_io     = psutil.disk_io_counters()
        disk_read   = (disk_io.read_bytes  - prev_disk.read_bytes)  / dt
        disk_write  = (disk_io.write_bytes - prev_disk.write_bytes) / dt
        prev_disk   = disk_io

        # Disco utilizzo
        disk_usage  = psutil.disk_usage("/")
        disk_used_pct = disk_usage.percent

        # Rete
        net       = psutil.net_io_counters()
        net_down  = (net.bytes_recv - prev_net.bytes_recv) / dt
        net_up    = (net.bytes_sent - prev_net.bytes_sent) / dt
        prev_net  = net

        # Temperatura (best effort — None su M1 senza osx-cpu-temp)
        temp = _temperature()

        payload = {
            "type":         "stats_update",
            "cpu_pct":      round(cpu_pct, 1),
            "mem_used_gb":  round(mem_used, 1),
            "mem_total_gb": round(mem_total, 1),
            "mem_pct":      round(mem_pct, 1),
            "disk_read":    _fmt_bytes(disk_read),
            "disk_write":   _fmt_bytes(disk_write),
            "disk_used_pct": round(disk_used_pct, 1),
            "net_down":     _fmt_bytes(net_down),
            "net_up":       _fmt_bytes(net_up),
            "temp_c":       round(temp, 1) if temp is not None else None,
        }

        await send_fn(payload)
