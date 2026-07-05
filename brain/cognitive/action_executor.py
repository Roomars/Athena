"""
ActionExecutor — Layer Azione del cognitive stack (ispirato a moeru-ai/airi).

Pattern: il LLM (Consapevolezza) non esegue mai azioni direttamente.
L'ActionExecutor valida, chiede approvazione se necessario, esegue con
retry e restituisce il risultato al layer superiore.

4 layer di Ari:
  1. Percezione   — classify(), entity extraction (complexity_router)
  2. Riflesso     — skill_router: match istantaneo per pattern noti
  3. Consapevolezza — LLM.stream() con contesto ridotto e pulito
  4. Azione       — ActionExecutor: esecuzione isolata, approval, retry
"""
import asyncio
import logging
from typing import Callable, Awaitable, Any

log = logging.getLogger("action_executor")

_MAX_RETRIES   = 2
_RETRY_DELAY_S = 0.5


class ActionExecutor:
    """
    Esegue skill con ciclo: validazione → approvazione → esecuzione → retry.
    Istanziato una volta in ws_handler con i riferimenti al canale approvazione.
    """

    def __init__(
        self,
        approval_fn:    Callable[[str, str], Awaitable[bool]] | None = None,
        always_allowed: set[str] | None = None,
    ):
        self._approval_fn    = approval_fn
        self._always_allowed = always_allowed if always_allowed is not None else set()

    async def execute(
        self,
        skill:            Any,
        user_input:       str,
        params:           dict,
        *,
        require_approval: bool = False,
        pre_message:      str  = "",
    ) -> str | None:
        """
        Esegue la skill e ritorna il risultato, o None se:
          - approvazione negata dall'utente
          - tutti i retry esauriti

        pre_message: testo da loggare prima dell'esecuzione (es. "Guardo lo schermo...").
        """
        if pre_message:
            log.info(pre_message)

        if require_approval and self._approval_fn:
            if skill.name not in self._always_allowed:
                approved = await self._approval_fn(skill.name, user_input[:120])
                if not approved:
                    log.info(f"skill '{skill.name}' negata dall'utente")
                    return None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                result = await skill.run(user_input, params)
                log.info(f"skill '{skill.name}' completata: {result[:80]}")
                return result
            except Exception as e:
                log.error(f"skill '{skill.name}' tentativo {attempt + 1}/{_MAX_RETRIES + 1}: {e}")
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_RETRY_DELAY_S)

        return f"[Errore esecuzione skill {skill.name} dopo {_MAX_RETRIES + 1} tentativi]"

    def grant_always(self, skill_name: str) -> None:
        """Aggiunge skill_name alla whitelist 'Consenti sempre'."""
        self._always_allowed.add(skill_name)
