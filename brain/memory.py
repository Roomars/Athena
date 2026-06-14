import logging

log = logging.getLogger("memory")

MAX_MESSAGES = 20


class WorkingMemory:
    """Sliding window in-process memory. FASE 4 aggiunge ChromaDB."""

    def __init__(self):
        self._messages: list[dict] = []

    def add(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})
        if len(self._messages) > MAX_MESSAGES:
            # Rimuove la coppia più vecchia (user+assistant) per mantenere coerenza
            self._messages = self._messages[-MAX_MESSAGES:]
            log.debug(f"working memory troncata a {MAX_MESSAGES} messaggi")

    def get(self) -> list[dict]:
        return list(self._messages)

    def clear(self):
        self._messages.clear()
        log.info("working memory azzerata")

    def __len__(self):
        return len(self._messages)


working_memory = WorkingMemory()
