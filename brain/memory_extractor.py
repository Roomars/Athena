import asyncio
import json
import logging
import time

from .llm import engine
from .memory_store import memory_store

log = logging.getLogger("memory_extractor")

_SYSTEM = "Sei un estrattore di fatti. Rispondi SOLO con JSON valido, senza testo aggiuntivo."

_FACT_PROMPT = """\
Analizza questo scambio e estrai fatti ESPLICITI sull'utente (solo ciò che ha detto direttamente, \
zero inferenze). Se non ci sono fatti nuovi rispondi con {{}}.

Formato richiesto:
{{"fatti": [{{"key": "chiave_breve", "value": "valore"}}]}}

Esempi di chiavi: nome, cognome, professione, citta, hobby, progetto_corrente, lingua_preferita, \
eta, animale_domestico, partner, figli, preferenze_musica, lavoro_attuale

Scambio:
Utente: {user}
Ari: {assistant}"""

_EPISODE_PROMPT = """\
Riassumi questa conversazione in una frase concisa (max 120 caratteri) che catturi \
l'argomento principale e l'esito. Rispondi SOLO con il testo del riassunto, niente altro.

Conversazione ({n} messaggi):
{excerpt}"""

_CONTRADICT_PROMPT = """\
Il fatto attuale in memoria è:
  {key}: {old_value}

Il nuovo valore estratto è:
  {key}: {new_value}

Questi due valori si contraddicono (uno esclude l'altro)? Rispondi SOLO con "si" o "no"."""


async def _llm_text(messages: list[dict], max_tokens: int = 200) -> str:
    raw = ""
    async for kind, token in engine.stream(messages, max_tokens=max_tokens, thinking=False):
        if kind == "chunk":
            raw += token
        elif kind == "done":
            break
    return raw.strip()


async def extract_and_save(user_msg: str, assistant_msg: str) -> None:
    """Estrae fatti dall'ultimo turno e li salva. Lancia gap detection e contradiction check."""
    try:
        prompt = _FACT_PROMPT.format(
            user=user_msg[:600],
            assistant=assistant_msg[:600],
        )
        raw = await _llm_text([
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ])

        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return

        data  = json.loads(raw[start:end])
        fatti = data.get("fatti", [])
        for f in fatti:
            key   = str(f.get("key",   "")).strip()
            value = str(f.get("value", "")).strip()
            if not key or not value:
                continue

            # Contradiction check: se il fatto esiste già con valore diverso
            existing = memory_store.get_facts().get(key)
            if existing and existing != value:
                asyncio.create_task(_check_contradiction(key, existing, value))

            memory_store.upsert_fact(key, value)
            log.info(f"memoria: '{key}' = '{value}'")

        # Gap detection: cerca riferimenti a cose sconosciute
        asyncio.create_task(_gap_detection(user_msg, assistant_msg))

    except Exception as e:
        log.debug(f"extract_and_save ignorato: {e}")


async def _check_contradiction(key: str, old_value: str, new_value: str) -> None:
    """Chiede all'LLM se old_value e new_value si contraddicono; se sì, aggiunge edge."""
    try:
        prompt = _CONTRADICT_PROMPT.format(key=key, old_value=old_value, new_value=new_value)
        answer = await _llm_text([
            {"role": "system", "content": "Rispondi solo con 'si' o 'no'."},
            {"role": "user",   "content": prompt},
        ], max_tokens=5)
        if answer.lower().startswith("s"):
            memory_store.add_relation(key, key, "Contradicts")
            log.info(f"contraddizione rilevata per '{key}': '{old_value}' vs '{new_value}'")
    except Exception as e:
        log.debug(f"_check_contradiction ignorato: {e}")


async def _gap_detection(user_msg: str, assistant_msg: str) -> None:
    """
    Rileva gap: se l'assistente ha detto "non lo so" o "non ricordo" riguardo a qualcosa,
    segna quella chiave come gap da colmare nelle prossime interazioni.
    """
    text = assistant_msg.lower()
    gap_signals = ["non lo so", "non ricordo", "non ne sono sicuro", "non ho informazioni"]
    if not any(sig in text for sig in gap_signals):
        return
    try:
        gap_prompt = f"""\
L'utente ha chiesto: "{user_msg[:200]}"
Ari ha risposto: "{assistant_msg[:300]}"

Ari non sapeva rispondere. Indica la chiave (una parola o breve sintagma in italiano) \
del fatto mancante. Rispondi SOLO con la chiave, niente altro."""
        key = await _llm_text([
            {"role": "system", "content": "Rispondi con una sola chiave breve."},
            {"role": "user",   "content": gap_prompt},
        ], max_tokens=20)
        key = key.strip().lower().replace(" ", "_")
        if key:
            memory_store.upsert_fact(f"_gap_{key}", "da_chiedere",
                                     tags=["gap"], confidence=0.0, source="gap_detection")
            log.info(f"gap rilevato: '{key}'")
    except Exception as e:
        log.debug(f"_gap_detection ignorato: {e}")


async def save_episode(messages: list[dict]) -> None:
    """Genera un riassunto LLM della conversazione e lo salva come episodio."""
    if len(messages) < 2:
        return
    try:
        # Estratto: ultimi 6 messaggi (3 turni)
        tail = messages[-6:]
        excerpt = "\n".join(
            f"{'Utente' if m['role']=='user' else 'Ari'}: {str(m['content'])[:200]}"
            for m in tail
        )
        prompt = _EPISODE_PROMPT.format(n=len(messages), excerpt=excerpt)
        summary = await _llm_text([
            {"role": "system", "content": "Rispondi in italiano con una sola frase concisa."},
            {"role": "user",   "content": prompt},
        ], max_tokens=80)
        summary = summary.strip().strip('"').strip("'")
        if not summary:
            # Fallback: primo messaggio utente
            summary = next((m["content"] for m in messages if m["role"] == "user"), "")[:120]
        if summary:
            keywords = list({w for w in _tokenize(summary) if len(w) > 3})[:8]
            memory_store.add_episode(summary=summary, message_count=len(messages), keywords=keywords)
            log.info(f"episodio salvato: '{summary[:60]}...' ({len(messages)} msg)")
    except Exception as e:
        log.debug(f"save_episode ignorato: {e}")


def decay_confidence() -> None:
    """
    Riduce la confidence dei fatti non aggiornati di recente.
    Chiamabile periodicamente (es. ogni 24h) o all'avvio.
    Decay: -0.05 per ogni settimana di inattività, floor a 0.1.
    """
    now = time.time()
    week = 7 * 24 * 3600
    rows = memory_store.get_facts_full()
    for r in rows:
        age_weeks = (now - r["updated_at"]) / week
        if age_weeks < 1:
            continue
        new_conf = max(0.1, r["confidence"] - 0.05 * age_weeks)
        if new_conf < r["confidence"] - 0.001:
            memory_store._db.execute(
                "UPDATE facts SET confidence=? WHERE key=?", (new_conf, r["key"])
            )
    memory_store._db.commit()
    log.debug("confidence decay applicato")


def _tokenize(text: str) -> list[str]:
    import re
    return re.split(r"[\s_\-/]+", text.lower())
