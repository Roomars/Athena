import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

MAX_HISTORY = 20

_CONSTITUTION = Path(__file__).parent.parent / "athena.md"


def _load_system_prompt() -> str:
    text = _CONSTITUTION.read_text(encoding="utf-8")
    # Estrae il contenuto del primo blocco ```...``` dopo "## System Prompt"
    match = re.search(r"## System Prompt\s.*?```\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: usa l'intera costituzione come contesto
    return text.strip()


def load_system_prompt() -> str:
    """Ricarica il prompt da disco (utile in sviluppo senza riavviare)."""
    return _load_system_prompt()


SYSTEM_PROMPT = _load_system_prompt()


@dataclass
class ConversationMemory:
    history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def to_messages(self) -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}] + list(self.history)

    def clear(self) -> None:
        self.history.clear()


memory = ConversationMemory()
