"""
Personalità vocali — riscrittura in-character del testo PRIMA del TTS.

Pattern adottato dal progetto Voicebox: il testo generato dall'LLM principale
viene facoltativamente riscritto "in personaggio" (solo tono/stile, mai il
contenuto) da un modello leggero, prima di essere passato al motore TTS.

Punto di iniezione (gestito dal task di wiring in ws_handler.py):
    full_response → _tts_text() → rewrite_in_character() → tts.speak()

Requisiti hard rispettati qui:
  1. persona_id == "nessuna" (o sconosciuta) → passthrough IMMEDIATO, zero
     latenza aggiunta, NESSUNA chiamata all'LLM.
  2. La riscrittura usa MODEL_FAST (Llama-3.2-3B-Instruct-4bit) per minimizzare
     la latenza prima che Ari parli.
  3. La riscrittura NON altera mai il contenuto informativo: solo tono/stile.
     Il system prompt lo impone esplicitamente.
  4. Qualsiasi errore → fallback silenzioso al testo originale. La pipeline TTS
     non deve mai bloccarsi o rompersi a causa della riscrittura.

--- Scelta implementativa (modello dedicato, NON il primario) ---
brain/llm.py NON espone una generazione "one-off" con un modello diverso da
quello caricato: switch_to()/load_async() SOSTITUISCONO il modello primario
(oggi Qwen3-14B), il che sarebbe una regressione (unload + reload costoso ad
ogni risposta parlata).

Per questo persona.py carica MODEL_FAST in modo pigro e indipendente, su un
proprio ThreadPoolExecutor a 1 worker. Come in llm.py, caricamento e
generazione avvengono sullo STESSO thread (gli stream Metal di MLX sono
thread-local: caricare e generare altrove causa "no stream gpu N"). Il modello
primario non viene mai toccato.

Costo/tradeoff: se e solo quando l'utente seleziona una persona diversa da
"nessuna", MODEL_FAST (~1.7 GB VRAM, 3B-4bit) viene caricato una volta e resta
residente. Con persona "nessuna" (default) non viene caricato nulla e il
comportamento è identico a oggi. La riscrittura avviene DOPO il completamento
della generazione primaria (tra _tts_text e tts.speak), quindi non è concorrente
con l'executor MLX principale: nessuna contesa GPU aggiuntiva durante lo stream.
"""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .llm import MODEL_FAST

log = logging.getLogger("persona")


# ──────────────────────────────────────────────────────────────────────────────
# Struttura dati
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Persona:
    """Una personalità vocale.

    id:            chiave stabile usata da settings/UI/WebSocket.
    nome:          etichetta leggibile mostrata nell'interfaccia.
    system_prompt: istruzioni di stile/tono per la riscrittura. Se None/"" la
                   persona è un passthrough (nessuna riscrittura, nessun LLM).
    """
    id: str
    nome: str
    system_prompt: str | None


# Istruzione base anteposta al system_prompt di ogni persona attiva.
# È il guard-rail che impedisce all'LLM di alterare il contenuto informativo:
# riscrive SOLO tono e stile, senza aggiungere, togliere o inventare fatti.
_REWRITE_GUARD = (
    "Sei un motore di riscrittura stilistica per un assistente vocale italiano. "
    "Ricevi un testo già scritto e lo riscrivi cambiando SOLO il tono e lo stile "
    "secondo le indicazioni di personalità qui sotto. "
    "REGOLE INVIOLABILI:\n"
    "- NON aggiungere, togliere o inventare alcuna informazione, cifra, nome o fatto.\n"
    "- Mantieni identico il contenuto informativo e la lingua (italiano).\n"
    "- Non aggiungere premesse, commenti, virgolette o meta-testo.\n"
    "- Il testo è destinato a essere letto ad alta voce: niente markdown, niente elenchi puntati.\n"
    "- Rispondi ESCLUSIVAMENTE con il testo riscritto, nient'altro.\n\n"
    "Indicazioni di personalità:\n"
)


# ──────────────────────────────────────────────────────────────────────────────
# Personas predefinite
# ──────────────────────────────────────────────────────────────────────────────

PERSONAS: dict[str, Persona] = {
    # Passthrough: comportamento identico a oggi, nessuna riscrittura, nessun LLM.
    "nessuna": Persona(
        id="nessuna",
        nome="Nessuna (voce naturale)",
        system_prompt=None,
    ),

    # Formale/professionale: sobria, cortese, precisa. Stile "maggiordomo Jarvis".
    "professionale": Persona(
        id="professionale",
        nome="Professionale",
        system_prompt=(
            "Tono formale, misurato e professionale, come un maggiordomo "
            "digitale competente. Frasi complete e cortesi, lessico preciso, "
            "nessuna esclamazione eccessiva. Dai del 'lei' con discrezione solo "
            "se già presente nel testo originale, altrimenti resta neutro. "
            "Concisione ed eleganza sopra ogni cosa."
        ),
    ),

    # Informale/amichevole: caldo, colloquiale, vicino.
    "amichevole": Persona(
        id="amichevole",
        nome="Amichevole",
        system_prompt=(
            "Tono caldo, informale e amichevole, come un amico fidato che dà "
            "una mano. Frasi scorrevoli e naturali, qualche espressione "
            "colloquiale, dai del 'tu'. Rimani sintetico e diretto, senza "
            "diventare sdolcinato o prolisso."
        ),
    ),

    # Arguta: ironia leggera e asciutta, senza mai sacrificare la chiarezza.
    "arguta": Persona(
        id="arguta",
        nome="Arguta",
        system_prompt=(
            "Tono brillante con un tocco di ironia asciutta ed elegante, alla "
            "Jarvis. Una battuta misurata è benvenuta, ma la chiarezza e la "
            "correttezza dell'informazione vengono sempre prima dello scherzo. "
            "Mai sarcasmo pesante, mai a scapito dell'utente."
        ),
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Motore leggero dedicato (lazy, indipendente dal modello primario)
# ──────────────────────────────────────────────────────────────────────────────

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="persona")
_load_lock = threading.Lock()
_fast_model = None
_fast_tokenizer = None
_load_failed = False  # se il caricamento fallisce, non ritentare a ogni chiamata


def _ensure_fast_loaded() -> bool:
    """Carica MODEL_FAST una sola volta, sul thread dell'executor persona.

    Ritorna True se il modello è pronto. Da chiamare SOLO dentro l'executor
    (caricamento e generazione devono stare sullo stesso thread — stream Metal
    thread-local). Idempotente e thread-safe.
    """
    global _fast_model, _fast_tokenizer, _load_failed
    if _fast_model is not None:
        return True
    if _load_failed:
        return False
    with _load_lock:
        if _fast_model is not None:
            return True
        if _load_failed:
            return False
        try:
            import os
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from mlx_lm import load as load_lm
            log.info(f"caricamento modello persona: {MODEL_FAST}")
            try:
                model, tokenizer = load_lm(MODEL_FAST)
            except Exception:
                # Ritenta consentendo il download se non è in cache offline.
                os.environ.pop("HF_HUB_OFFLINE", None)
                model, tokenizer = load_lm(MODEL_FAST)
            _fast_model = model
            _fast_tokenizer = tokenizer
            log.info(f"modello persona pronto: {MODEL_FAST}")
            return True
        except Exception as e:
            log.error(f"caricamento modello persona fallito: {e}")
            _load_failed = True
            return False


def _blocking_generate(system_prompt: str, user_text: str, max_tokens: int) -> str | None:
    """Generazione sincrona sul thread dell'executor persona.

    Ritorna il testo generato oppure None in caso di problemi o output vuoto.
    Da chiamare SOLO dentro l'executor (Metal stream thread-local).
    """
    if not _ensure_fast_loaded():
        return None
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        tokenizer = (
            _fast_tokenizer.tokenizer
            if hasattr(_fast_tokenizer, "tokenizer")
            else _fast_tokenizer
        )
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # Riuso dello stesso stile di chiamata di llm.py (stream_generate mlx-lm),
        # accumulando i token: serve il testo completo prima di parlare.
        from mlx_lm import stream_generate
        out = ""
        for resp in stream_generate(
            _fast_model, _fast_tokenizer, prompt=prompt, max_tokens=max_tokens
        ):
            out += resp.text

        out = out.strip()
        return out if out else None
    except Exception as e:
        log.error(f"generazione persona fallita: {e}")
        return None
    finally:
        # Libera la Metal cache accumulata (come in llm.py).
        try:
            import mlx.core as mx
            import gc
            mx.metal.clear_cache()
            gc.collect()
        except Exception:
            pass


def _blocking_rewrite(system_prompt: str, text: str, max_tokens: int) -> str:
    """Riscrittura sincrona sul thread dell'executor persona.

    Ritorna il testo riscritto, oppure il testo originale in caso di problemi.
    Wrapper sottile su _blocking_generate: preserva il fallback al testo
    originale che la pipeline TTS si aspetta.
    """
    result = _blocking_generate(system_prompt, text, max_tokens)
    return result if result else text


# ──────────────────────────────────────────────────────────────────────────────
# API pubblica
# ──────────────────────────────────────────────────────────────────────────────

async def rewrite_in_character(text: str, persona_id: str) -> str:
    """Riscrive `text` nello stile della persona `persona_id`, prima del TTS.

    Passthrough (nessuna latenza, nessun LLM) se:
      - persona_id == "nessuna"
      - persona_id non è in PERSONAS
      - la persona non ha un system_prompt
      - text è vuoto

    In tutti gli altri casi chiama MODEL_FAST per riscrivere SOLO tono/stile.
    Qualsiasi errore → ritorna il testo originale (fallback silenzioso).
    """
    if not text or not text.strip():
        return text

    persona = PERSONAS.get(persona_id)
    if persona is None or not persona.system_prompt:
        return text

    system_prompt = _REWRITE_GUARD + persona.system_prompt
    # La riscrittura non deve allungare il testo: tetto proporzionale all'input
    # (~1 token ogni 3 char in italiano) più un margine, con un cap ragionevole.
    max_tokens = min(512, max(64, len(text) // 3 + 96))

    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, _blocking_rewrite, system_prompt, text, max_tokens
        )
    except Exception as e:
        log.error(f"rewrite_in_character fallita: {e}")
        return text


async def generate_fast(
    system_prompt: str, user_text: str, max_tokens: int = 200
) -> str | None:
    """Genera testo con MODEL_FAST su executor dedicato, indipendente dal modello primario.

    Ritorna None (senza sollevare mai eccezioni) se:
      - user_text è vuoto o blank
      - il caricamento di MODEL_FAST fallisce
      - la generazione lancia un'eccezione
      - l'output è vuoto dopo strip

    Pensata per task strutturati e leggeri (estrazione JSON breve, si/no,
    riassunto corto) dove la latenza conta più della qualità massima.
    Il chiamante decide il proprio fallback in caso di None.
    """
    if not user_text or not user_text.strip():
        return None
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, _blocking_generate, system_prompt, user_text, max_tokens
        )
    except Exception as e:
        log.error(f"generate_fast fallita: {e}")
        return None


def available_personas() -> list[dict]:
    """Lista serializzabile (id, nome) per l'esposizione a UI/WebSocket."""
    return [{"id": p.id, "nome": p.nome} for p in PERSONAS.values()]
