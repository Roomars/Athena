import asyncio
import logging
import threading
from typing import AsyncGenerator

log = logging.getLogger("llm")

# Gemma 4 31B — testo + vision in un unico modello (mlx-vlm)
MODEL_PRIMARY = "mlx-community/gemma-4-31b-it-4bit"
MODEL_FAST    = "mlx-community/gemma-4-12b-it-4bit"   # già scaricato (vecchio vision)
MODEL_HEAVY   = "mlx-community/gemma-4-31b-it-4bit"


class LLMEngine:
    def __init__(self):
        self._model     = None
        self._processor = None
        self._config    = None
        self._model_id: str | None = None
        self._loading = False
        self._lock    = threading.Lock()
        self.on_ready: list = []

    # ------------------------------------------------------------------
    # Caricamento
    # ------------------------------------------------------------------

    def load_async(self, model_id: str = MODEL_PRIMARY):
        """Carica il modello in un thread separato — non blocca FastAPI."""
        def _work():
            with self._lock:
                self._loading = True
                log.info(f"caricamento: {model_id}")
                try:
                    import os
                    from mlx_vlm import load
                    from mlx_vlm.utils import load_config
                    os.environ.setdefault("HF_HUB_OFFLINE", "1")
                    try:
                        model, processor = load(model_id)
                        config = load_config(model_id)
                    except Exception:
                        os.environ.pop("HF_HUB_OFFLINE", None)
                        model, processor = load(model_id)
                        config = load_config(model_id)
                    self._model     = model
                    self._processor = processor
                    self._config    = config
                    self._model_id  = model_id
                    self._loading   = False
                    log.info(f"modello pronto: {model_id}")
                    for cb in self.on_ready:
                        cb(model_id)
                except Exception as e:
                    log.error(f"errore caricamento {model_id}: {e}")
                    if model_id != MODEL_FAST:
                        log.info(f"fallback a {MODEL_FAST}")
                        self._loading = False
                        self.load_async(MODEL_FAST)
                        return
                finally:
                    self._loading = False

        threading.Thread(target=_work, daemon=True).start()

    @property
    def is_ready(self) -> bool:
        return self._model is not None and not self._loading

    @property
    def model_id(self) -> str | None:
        return self._model_id

    # Esposti a vision.py per condividere il modello caricato
    @property
    def model(self):
        return self._model

    @property
    def processor(self):
        return self._processor

    @property
    def config(self):
        return self._config

    # ------------------------------------------------------------------
    # Generazione streaming (text-only)
    # ------------------------------------------------------------------

    async def stream(
        self,
        messages: list[dict],
        max_tokens: int = 2048,
        thinking: bool = False,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """
        Async generator. Yields (kind, text):
          ("thinking", "")   — Ari sta ragionando
          ("chunk", token)   — token visibile
          ("done", "")       — generazione completata
        """
        if not self.is_ready:
            yield ("chunk", "Sto caricando il modello, un momento...")
            yield ("done", "")
            return

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _generate():
            try:
                from mlx_vlm import stream_generate

                # Chat template — usa il tokenizer interno del processor
                tokenizer = (
                    self._processor.tokenizer
                    if hasattr(self._processor, "tokenizer")
                    else self._processor
                )
                try:
                    prompt = tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=thinking,
                    )
                except TypeError:
                    prompt = tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                    )

                in_think = False
                think_buf = ""

                for resp in stream_generate(
                    self._model,
                    self._processor,
                    prompt=prompt,
                    image=None,
                    max_tokens=max_tokens,
                    enable_thinking=thinking,
                ):
                    token = resp.text

                    if not in_think and "<think>" in token:
                        in_think = True

                    if in_think:
                        think_buf += token
                        loop.call_soon_threadsafe(queue.put_nowait, ("thinking", ""))
                        if "</think>" in think_buf:
                            in_think = False
                            after = think_buf.split("</think>", 1)[1]
                            think_buf = ""
                            if after.strip():
                                loop.call_soon_threadsafe(queue.put_nowait, ("chunk", after))
                        continue

                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", token))

            except Exception as e:
                log.error(f"errore generazione: {e}")
                loop.call_soon_threadsafe(queue.put_nowait, ("chunk", f"[errore: {e}]"))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("done", ""))

        threading.Thread(target=_generate, daemon=True).start()

        while True:
            item = await queue.get()
            yield item
            if item[0] == "done":
                break

    # ------------------------------------------------------------------
    # Generazione con immagine (usato da vision.py)
    # ------------------------------------------------------------------

    def generate_vision(self, image_pil, prompt: str, max_tokens: int = 1024) -> str:
        """Genera testo da immagine PIL + prompt. Sincrono — chiamare in executor."""
        if not self.is_ready:
            return "Modello non ancora pronto."
        try:
            from mlx_vlm import generate
            from mlx_vlm import apply_chat_template

            formatted = apply_chat_template(
                self._processor, self._config, prompt, num_images=1
            )
            return generate(
                self._model, self._processor, image_pil, formatted,
                max_tokens=max_tokens, verbose=False,
            ).strip()
        except Exception as e:
            log.error(f"errore generazione vision: {e}")
            return f"Errore durante l'analisi: {e}"


engine = LLMEngine()
