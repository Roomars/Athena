from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class Notification:
    title: str
    body:  str
    speak: bool = True


class Trigger(ABC):
    cooldown: float = 1800  # secondi minimi tra due attivazioni dello stesso trigger

    def __init__(self):
        self._last_fired: float = 0

    def _can_fire(self) -> bool:
        return time.time() - self._last_fired > self.cooldown

    def _mark_fired(self):
        self._last_fired = time.time()

    @abstractmethod
    async def check(self) -> Notification | None: ...
