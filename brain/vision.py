"""
Motore vision — Gemma 4 31B (VLM) caricato on-demand + YOLO structured detection.

analyze()            → testo libero
analyze_structured() → dict {description, apps, objects, zones, anomalies, answer}

Il modello di default dell'engine è text-only (leggero). La vision richiede un
VLM: per questo si carica MODEL_HEAVY (Gemma 4 31B) SOLO al momento del bisogno
via engine.ensure_vision_ready(), e al termine si torna al modello preferito
dall'utente. Tradeoff consapevole: ~20-30s di reload a ogni uso della vision,
in cambio di molta meno RAM occupata a riposo.
"""
import base64
import io
import json
import logging

log = logging.getLogger("vision")


def is_ready() -> bool:
    from .llm import engine
    return engine.is_ready


async def _restore_preferred() -> None:
    """Torna al modello preferito dall'utente dopo l'uso della vision."""
    from .llm import engine
    preferred = engine.preferred_id
    if preferred and preferred != engine.model_id:
        log.info(f"vision terminata: ripristino {preferred}")
        engine.switch_to(preferred, "mlx")


async def analyze(image_b64: str, prompt: str) -> str:
    """Descrizione testuale libera. Carica il VLM on-demand e poi ripristina."""
    import asyncio
    from .llm import engine

    ok = await engine.ensure_vision_ready()
    if not ok:
        return "Modello vision non disponibile — riprova tra qualche secondo."

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(engine._executor, _analyze_sync, image_b64, prompt)
    finally:
        await _restore_preferred()


async def analyze_structured(image_b64: str, user_prompt: str) -> dict:
    """
    Analisi strutturata in due stadi:
      1. YOLO (cpu, ~50ms) → contesto oggetti/zone
      2. Gemma 4 31B (VLM caricato on-demand) con prompt JSON strutturato
    """
    import asyncio
    from .llm import engine
    from .vision_detector import detect, detection_to_context

    loop = asyncio.get_event_loop()
    det      = await loop.run_in_executor(None, detect, image_b64)
    yolo_ctx = detection_to_context(det)

    ok = await engine.ensure_vision_ready()
    if not ok:
        return _parse_structured("", det, user_prompt)

    structured_prompt = _build_structured_prompt(user_prompt, yolo_ctx)
    try:
        raw = await loop.run_in_executor(engine._executor, _analyze_sync, image_b64, structured_prompt)
    finally:
        await _restore_preferred()

    return _parse_structured(raw, det, user_prompt)


def _analyze_sync(image_b64: str, prompt: str) -> str:
    from PIL import Image
    from .llm import engine

    if not engine.is_ready:
        return "Modello non disponibile — riprova tra qualche secondo."

    try:
        image_data = base64.b64decode(image_b64)
        image      = Image.open(io.BytesIO(image_data)).convert("RGB")
    except Exception as e:
        log.error(f"Errore decodifica immagine: {e}")
        return "Errore: immagine non valida."

    return engine.generate_vision(image, prompt)


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
    """Estrae il JSON dalla risposta. Fallback graceful se malformato."""
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            result = json.loads(raw[start:end])
            if det.get("counts") and not result.get("objects"):
                result["objects"] = list(det["counts"].keys())
            if det.get("zones") and not result.get("zones"):
                result["zones"] = det["zones"]
            if det.get("anomalies") and not result.get("anomalies"):
                result["anomalies"] = det["anomalies"]
            return result
        except json.JSONDecodeError:
            pass

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
