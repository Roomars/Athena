import asyncio
import json
import logging

from .llm import engine
from .memory_store import memory_store

log = logging.getLogger("memory_extractor")

_SYSTEM = "Sei un estrattore di fatti. Rispondi SOLO con JSON valido, senza testo aggiuntivo."

_PROMPT = """\
Analizza questo scambio e estrai fatti ESPLICITI sull'utente (solo ciò che ha detto direttamente, \
zero inferenze). Se non ci sono fatti nuovi rispondi con {{}}.

Formato richiesto:
{{"fatti": [{{"key": "chiave_breve", "value": "valore"}}]}}

Esempi di chiavi: nome, cognome, professione, citta, hobby, progetto_corrente, lingua_preferita, \
eta, animale_domestico, partner, figli, preferenze_musica, lavoro_attuale

Scambio:
Utente: {user}
Ari: {assistant}"""


async def extract_and_save(user_msg: str, assistant_msg: str) -> None:
    """Lancia l'estrazione fatti in background — non blocca la risposta principale."""
    try:
        prompt = _PROMPT.format(
            user=user_msg[:600],
            assistant=assistant_msg[:600],
        )
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ]

        raw = ""
        async for kind, token in engine.stream(messages, max_tokens=256, thinking=False):
            if kind == "chunk":
                raw += token
            elif kind == "done":
                break

        # Trova il blocco JSON nella risposta (ignora eventuale testo)
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return

        data  = json.loads(raw[start:end])
        fatti = data.get("fatti", [])
        for f in fatti:
            key   = str(f.get("key",   "")).strip()
            value = str(f.get("value", "")).strip()
            if key and value:
                memory_store.upsert_fact(key, value)
                log.info(f"memoria: '{key}' = '{value}'")

    except Exception as e:
        log.debug(f"extract_and_save ignorato: {e}")


async def save_episode(messages: list[dict]) -> None:
    """Salva un riassunto della sessione corrente al momento della disconnessione."""
    if len(messages) < 2:
        return
    try:
        # Usa il primo messaggio utente come hook del riassunto
        first_user = next((m["content"] for m in messages if m["role"] == "user"), "")
        summary = first_user[:120].strip()
        if not summary:
            return
        memory_store.add_episode(
            summary=summary,
            message_count=len(messages),
        )
        log.info(f"episodio salvato: '{summary[:60]}...' ({len(messages)} msg)")
    except Exception as e:
        log.debug(f"save_episode ignorato: {e}")
