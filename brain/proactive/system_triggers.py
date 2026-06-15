import asyncio
import re
import subprocess

import psutil

from ._base import Trigger, Notification


class BatteryTrigger(Trigger):
    """Avvisa quando la batteria scende sotto soglia e non è in carica."""
    cooldown   = 1800   # 30 min
    threshold  = 20     # %

    async def check(self) -> Notification | None:
        if not self._can_fire():
            return None
        try:
            out = subprocess.check_output(["pmset", "-g", "batt"], text=True)
            m   = re.search(r"(\d+)%", out)
            if not m:
                return None
            pct      = int(m.group(1))
            charging = "AC" in out and "discharging" not in out.lower()
            if pct <= self.threshold and not charging:
                self._mark_fired()
                return Notification(
                    title="Batteria scarica",
                    body=f"Batteria al {pct}% — collegati alla corrente.",
                )
        except Exception:
            pass
        return None


class CPUTrigger(Trigger):
    """Avvisa quando la CPU è sostenuta oltre soglia per due check consecutivi."""
    cooldown     = 600    # 10 min
    threshold    = 90     # %

    def __init__(self):
        super().__init__()
        self._consecutive = 0

    async def check(self) -> Notification | None:
        if not self._can_fire():
            return None
        loop = asyncio.get_event_loop()
        cpu  = await loop.run_in_executor(None, lambda: psutil.cpu_percent(interval=1))
        if cpu > self.threshold:
            self._consecutive += 1
            if self._consecutive >= 2:
                self._consecutive = 0
                self._mark_fired()
                return Notification(
                    title="CPU al massimo",
                    body=f"CPU al {cpu:.0f}% — qualcosa sta lavorando intensamente.",
                )
        else:
            self._consecutive = 0
        return None


class MemoryTrigger(Trigger):
    """Avvisa quando la RAM supera la soglia."""
    cooldown   = 1800   # 30 min
    threshold  = 90     # %  (32 GB → soglia a 90% = ~29 GB)

    async def check(self) -> Notification | None:
        if not self._can_fire():
            return None
        vm  = psutil.virtual_memory()
        pct = vm.percent
        if pct > self.threshold:
            used  = vm.used  / (1024 ** 3)
            total = vm.total / (1024 ** 3)
            self._mark_fired()
            return Notification(
                title="Memoria quasi piena",
                body=f"RAM al {pct:.0f}% ({used:.1f}/{total:.0f} GB usati).",
            )
        return None
