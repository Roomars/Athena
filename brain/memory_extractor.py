import asyncio
import json
import logging
import time

from .memory_store import memory_store
from .persona import generate_fast

log = logging.getLogger("memory_extractor")

# Chiavi dei fatti nuovi estratti dall'inizio della conversazione corrente,
# consumate da save_episode() per creare edge DerivedFrom (episodio -> fatto).
# Instanza singola: come working_memory/memory_store, il daemon è single-user.
_session_keys: list[str] = []

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
    system_prompt = next(
        (m["content"] for m in messages if m.get("role") == "system"), ""
    )
    user_prompt = next(
        (m["content"] for m in messages if m.get("role") == "user"), ""
    )
    result = await generate_fast(system_prompt, user_prompt, max_tokens=max_tokens)
    return (result or "").strip()


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

            old_value = memory_store.get_facts().get(key)
            hist_node_id = memory_store.upsert_fact(key, value)
            log.info(f"memoria: '{key}' = '{value}'")

            if hist_node_id and old_value and old_value != value:
                # Valore cambiato: upsert_fact ha già creato l'edge Supersedes
                # (key -> hist_node_id). Verifica LLM se è una vera contraddizione
                # (in tal caso l'edge viene promosso a Contradicts).
                asyncio.create_task(_check_contradiction(key, old_value, value, hist_node_id))
            elif hist_node_id is None:
                # Fatto nuovo (non un aggiornamento): cerca fatti correlati.
                asyncio.create_task(_link_related(key, value))
                _session_keys.append(key)

        # Gap detection: cerca riferimenti a cose sconosciute
        asyncio.create_task(_gap_detection(user_msg, assistant_msg))

    except Exception as e:
        log.debug(f"extract_and_save ignorato: {e}")


async def _check_contradiction(key: str, old_value: str, new_value: str, hist_node_id: str) -> None:
    """Chiede all'LLM se old_value e new_value si contraddicono.

    upsert_fact ha già creato un edge Supersedes (key -> hist_node_id), il
    caso di default per un valore che cambia. Se l'LLM conferma che è una
    vera contraddizione (non solo una correzione/aggiornamento), l'edge
    viene promosso a Contradicts.
    """
    try:
        prompt = _CONTRADICT_PROMPT.format(key=key, old_value=old_value, new_value=new_value)
        answer = await _llm_text([
            {"role": "system", "content": "Rispondi solo con 'si' o 'no'."},
            {"role": "user",   "content": prompt},
        ], max_tokens=5)
        if answer.lower().startswith("s"):
            memory_store.add_relation(key, hist_node_id, "Contradicts")
            log.warning(f"contraddizione rilevata per '{key}': '{old_value}' vs '{new_value}'")
    except Exception as e:
        log.debug(f"_check_contradiction ignorato: {e}")


async def _link_related(key: str, value: str) -> None:
    """Cerca fatti semanticamente correlati (hybrid BM25+TF-IDF già presente
    in memory_store.search_facts) e crea edge RelatesTo verso i migliori 2
    candidati — solo per fatti nuovi, per non intasare il grafo ad ogni update."""
    try:
        loop = asyncio.get_event_loop()
        candidates = await loop.run_in_executor(None, memory_store.search_facts, value, 4)
        added = 0
        for c in candidates:
            other_key = c.get("key", "")
            if other_key and other_key != key:
                memory_store.add_relation(key, other_key, "RelatesTo")
                added += 1
                if added >= 2:
                    break
        if added:
            log.info(f"RelatesTo: '{key}' collegato a {added} fatti correlati")
    except Exception as e:
        log.debug(f"_link_related ignorato: {e}")


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
            episode_id = memory_store.add_episode(summary=summary, message_count=len(messages), keywords=keywords)
            log.info(f"episodio salvato: '{summary[:60]}...' ({len(messages)} msg)")

            # DerivedFrom: collega l'episodio ai fatti nuovi estratti durante
            # questa conversazione (episodio -> fatto, "il fatto deriva da qui").
            if _session_keys:
                episode_node = f"episode#{episode_id}"
                for key in dict.fromkeys(_session_keys):  # dedup preservando ordine
                    memory_store.add_relation(episode_node, key, "DerivedFrom")
                log.info(f"DerivedFrom: episodio collegato a {len(set(_session_keys))} fatti")
                _session_keys.clear()
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
