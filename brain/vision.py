"""
Motore vision — Gemma 4 12B via mlx-vlm + YOLO structured detection.

analyze()            → testo libero (comportamento originale)
analyze_structured() → dict {description, apps, objects, zones, anomalies, answer}
"""
import base64
import io
import json
import logging
import threading

log = logging.getLogger("vision")

# ID modello — verifica disponibilità su https://huggingface.co/mlx-community
MODEL_ID = "mlx-community/gemma-4-12b-it-4bit"

_model     = None
_processor = None
_config    = None
_lock      = threading.Lock()
_loading   = False


def _load() -> bool:
    global _model, _processor, _config, _loading
    with _lock:
        if _model is not None:
            return True
        if _loading:
            return False
        _loading = True

    try:
        log.info(f"Caricamento modello vision: {MODEL_ID}")
        from mlx_vlm import load
        from mlx_vlm.utils import load_config
        model, processor = load(MODEL_ID)
        config = load_config(MODEL_ID)
        with _lock:
            _model     = model
            _processor = processor
            _config    = config
            _loading   = False
        log.info("Modello vision pronto.")
        return True
    except Exception as e:
        log.error(f"Errore caricamento vision model: {e}")
        with _lock:
            _loading = False
        return False


def is_ready() -> bool:
    return _model is not None


async def analyze(image_b64: str, prompt: str) -> str:
    """Descrizione testuale libera (comportamento originale)."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_sync, image_b64, prompt)


async def analyze_structured(image_b64: str, user_prompt: str) -> dict:
    """
    Analisi strutturata in due stadi:
      1. YOLO (MPS, ~50ms) → objects/zones/anomalies come contesto
      2. Gemma con prompt JSON → {description, apps, objects, zones, anomalies, answer}
    """
    import asyncio
    from .vision_detector import detect, detection_to_context

    # Stadio 1: YOLO in executor (non blocca event loop)
    loop = asyncio.get_event_loop()
    det  = await loop.run_in_executor(None, detect, image_b64)
    yolo_ctx = detection_to_context(det)

    # Stadio 2: Gemma con contesto strutturato
    structured_prompt = _build_structured_prompt(user_prompt, yolo_ctx)
    raw = await loop.run_in_executor(None, _analyze_sync, image_b64, structured_prompt)

    return _parse_structured(raw, det, user_prompt)


def _build_structured_prompt(user_prompt: str, yolo_ctx: str) -> str:
    ctx_block = f"\nDati rilevamento rapido:\n{yolo_ctx}\n" if yolo_ctx else ""
    return f"""\
{ctx_block}
Analizza questo screenshot e rispondi in JSON valido con questa struttura esatta:
{{
  "description": "descrizione breve dello schermo in italiano (max 2 frasi)",
  "apps": ["lista delle app/finestre visibili"],
  "objects": ["oggetti fisici visibili (persone, dispositivi, ecc.)"],
  "zones": {{"top": "...", "bottom": "...", "center": "..."}},
  "anomalies": ["elementi inattesi o problematici, lista vuota se tutto normale"],
  "answer": "risposta diretta alla domanda dell'utente in italiano"
}}

Domanda dell'utente: {user_prompt}

Rispondi SOLO con il JSON, niente testo fuori dal blocco JSON."""


def _parse_structured(raw: str, det: dict, user_prompt: str) -> dict:
    """Estrae il JSON dalla risposta Gemma. Fallback graceful se malformato."""
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            result = json.loads(raw[start:end])
            # Arricchisce con i dati YOLO grezzi se Gemma non li ha inclusi
            if det.get("counts") and not result.get("objects"):
                result["objects"] = list(det["counts"].keys())
            if det.get("zones") and not result.get("zones"):
                result["zones"] = det["zones"]
            if det.get("anomalies") and not result.get("anomalies"):
                result["anomalies"] = det["anomalies"]
            return result
        except json.JSONDecodeError:
            pass

    # Fallback: restituisce testo libero come answer
    fallback_answer = raw.strip() if raw else f"Non riesco ad analizzare lo schermo per: {user_prompt}"
    return {
        "description": raw[:300] if raw else "Analisi non disponibile.",
        "apps":        [],
        "objects":     list((det.get("counts") or {}).keys()),
        "zones":       det.get("zones", {}),
        "anomalies":   det.get("anomalies", []),
        "answer":      fallback_answer,
    }


def structured_to_text(result: dict) -> str:
    """Converte il dict strutturato in testo naturale per TTS e chat."""
    parts = []
    if result.get("answer"):
        parts.append(result["answer"])
    if result.get("anomalies"):
        parts.append("Anomalie rilevate: " + ", ".join(result["anomalies"]) + ".")
    if result.get("apps"):
        apps = result["apps"]
        if len(apps) <= 4:
            parts.append("App visibili: " + ", ".join(apps) + ".")
    return " ".join(parts) if parts else result.get("description", "Schermo analizzato.")


def _analyze_sync(image_b64: str, prompt: str) -> str:
    from PIL import Image

    if not _load():
        return "Modello vision non disponibile — riprova tra qualche secondo."

    try:
        image_data = base64.b64decode(image_b64)
        image      = Image.open(io.BytesIO(image_data)).convert("RGB")
    except Exception as e:
        log.error(f"Errore decodifica immagine: {e}")
        return "Errore: immagine non valida."

    try:
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template

        formatted = apply_chat_template(
            _processor, _config, prompt, num_images=1
        )
        result = generate(
            _model, _processor, image, formatted,
            max_tokens=1024, verbose=False,
        )
        return result.strip()
    except Exception as e:
        log.error(f"Errore inferenza vision: {e}")
        return f"Errore durante l'analisi dello schermo: {e}"
