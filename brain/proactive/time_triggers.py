from datetime import datetime

from ._base import Trigger, Notification
from ..memory_store import memory_store


class MorningGreetingTrigger(Trigger):
    """Saluto mattutino personalizzato — una volta al giorno alle 9:00."""
    cooldown     = 86400   # 24h
    trigger_hour = 9
    trigger_window = 5     # minuti entro cui può scattare

    async def check(self) -> Notification | None:
        if not self._can_fire():
            return None
        now = datetime.now()
        if now.hour != self.trigger_hour or now.minute >= self.trigger_window:
            return None

        facts = memory_store.get_facts()
        nome  = facts.get("nome", "")
        saluto = f"Buongiorno{', ' + nome if nome else ''}!"

        self._mark_fired()
        return Notification(
            title="Buongiorno",
            body=f"{saluto} Pronto per iniziare?",
        )


class EveningCheckInTrigger(Trigger):
    """Check-in serale alle 18:00 — una volta al giorno."""
    cooldown     = 86400
    trigger_hour = 18
    trigger_window = 5

    async def check(self) -> Notification | None:
        if not self._can_fire():
            return None
        now = datetime.now()
        if now.hour != self.trigger_hour or now.minute >= self.trigger_window:
            return None

        self._mark_fired()
        return Notification(
            title="Fine giornata",
            body="Come è andata oggi? Posso aiutarti con qualcosa prima di staccare?",
        )
