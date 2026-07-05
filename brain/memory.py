import logging

log = logging.getLogger("memory")

MAX_MESSAGES = 20
MAX_CHARS    = 10_000  # ~2500 token: riduce KV cache durante la generazione


class WorkingMemory:
    """Sliding window in-process memory. FASE 4 aggiunge ChromaDB."""

    def __init__(self):
        self._messages: list[dict] = []

    def add(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})

        # Pruning 1: numero massimo di messaggi
        if len(self._messages) > MAX_MESSAGES:
            self._messages = self._messages[-MAX_MESSAGES:]

        # Pruning 2: lunghezza totale — rimuove coppie più vecchie finché
        # il contesto rientra nel budget. Mantiene almeno 2 messaggi (ultimo scambio).
        while len(self._messages) > 2:
            total = sum(len(m["content"]) for m in self._messages)
            if total <= MAX_CHARS:
                break
            self._messages = self._messages[2:]  # rimuove coppia user+assistant più vecchia
            log.debug(f"working memory pruned per char limit (ora {len(self._messages)} msg)")

    def get(self) -> list[dict]:
        return list(self._messages)

    def clear(self):
        self._messages.clear()
        log.info("working memory azzerata")

    def __len__(self):
        return len(self._messages)


working_memory = WorkingMemory()
