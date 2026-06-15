"""
Motore vision — Gemma 4 12B via mlx-vlm.
Caricamento lazy: il modello viene caricato solo alla prima richiesta.
"""
import base64
import io
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
    """
    Riceve un'immagine in base64 e un prompt testuale.
    Ritorna la descrizione generata da Gemma 4 12B.
    Blocca il thread solo durante l'inferenza (eseguita via run_in_executor).
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_sync, image_b64, prompt)


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
