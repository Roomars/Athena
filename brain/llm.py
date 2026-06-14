import asyncio
import logging
import threading
from typing import AsyncGenerator

log = logging.getLogger("llm")

# Modelli MLX disponibili (in ordine di preferenza)
MODEL_PRIMARY = "mlx-community/Qwen3-14B-4bit"
MODEL_FAST    = "mlx-community/Qwen3-4B-4bit"
MODEL_HEAVY   = "mlx-community/Qwen2.5-32B-4bit"


class LLMEngine:
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_id: str | None = None
        self._loading = False
        self._lock = threading.Lock()
        self.on_ready: list = []  # callbacks

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
                    from mlx_lm import load
                    # Usa cache locale — evita network check HuggingFace ad ogni avvio
                    os.environ.setdefault("HF_HUB_OFFLINE", "1")
                    try:
                        self._model, self._tokenizer = load(model_id)
                    except Exception:
                        # Modello non in cache — scarica dalla rete
                        os.environ.pop("HF_HUB_OFFLINE", None)
                        self._model, self._tokenizer = load(model_id)
                    self._model_id = model_id
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

    # ------------------------------------------------------------------
    # Generazione streaming
    # ------------------------------------------------------------------

    async def stream(
        self,
        messages: list[dict],
        max_tokens: int = 2048,
        thinking: bool = False,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """
        Async generator. Yields (kind, text):
          ("thinking", "")   — Ari sta ragionando (non mostrare)
          ("chunk", token)   — token visibile da streamare
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
                from mlx_lm import stream_generate

                # Applica chat template
                try:
                    prompt = self._tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=thinking,
                    )
                except TypeError:
                    # Tokenizer non supporta enable_thinking
                    prompt = self._tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                    )

                in_think = False
                think_buf = ""

                for resp in stream_generate(
                    self._model, self._tokenizer,
                    prompt=prompt,
                    max_tokens=max_tokens,
                ):
                    token = resp.text

                    # Filtra blocchi <think>...</think>
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


engine = LLMEngine()
