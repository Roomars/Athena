import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

log = logging.getLogger("llm")

# Modello di default: testo-only, leggero (mlx-lm). La vision NON è più
# sempre caricata: Gemma VLM viene ricaricato on-demand (vedi ensure_vision_ready).
MODEL_PRIMARY = "mlx-community/Qwen3-14B-4bit"                 # testo-only (mlx-lm)
MODEL_FAST    = "mlx-community/Llama-3.2-3B-Instruct-4bit"     # fallback leggero (mlx-lm)
MODEL_HEAVY   = "mlx-community/gemma-4-31b-it-4bit"            # VLM — unico usato per vision

# Registro modelli: quali preset sono vision-language (mlx-vlm) e quali
# text-only (mlx-lm). Tutto ciò che non è qui è trattato come text-only.
VLM_MODELS = {
    "mlx-community/gemma-4-31b-it-4bit",
    "mlx-community/gemma-4-12b-it-4bit",
}


def is_vlm(model_id: str | None) -> bool:
    """True se il modello va caricato/generato con mlx-vlm (vision+testo)."""
    return model_id in VLM_MODELS


class LLMEngine:
    def __init__(self):
        self._model     = None
        self._processor = None
        self._config    = None
        self._model_id: str | None = None
        # Modello scelto esplicitamente dall'utente (via Settings/switch_to).
        # Distinto dal modello effettivamente caricato: la vision on-demand
        # carica temporaneamente MODEL_HEAVY e poi torna a _preferred_id.
        self._preferred_id: str = MODEL_PRIMARY
        self._loading = False
        self._lock    = threading.Lock()
        self.on_ready: list = []
        # Thread singolo persistente: MLX Metal streams sono thread-local.
        # Caricare e generare nello stesso thread evita "no stream gpu N".
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mlx")
        # Backend: "mlx" | "openrouter"
        self._backend:         str       = "mlx"
        self._openrouter_key:  str | None = None
        self._openrouter_model: str | None = None

    # ------------------------------------------------------------------
    # Caricamento
    # ------------------------------------------------------------------

    def load_async(self, model_id: str = MODEL_PRIMARY):
        """Carica il modello nell'executor MLX dedicato — non blocca FastAPI."""
        def _work():
            with self._lock:
                self._loading = True
                log.info(f"caricamento: {model_id}")
                try:
                    import os
                    os.environ.setdefault("HF_HUB_OFFLINE", "1")

                    if is_vlm(model_id):
                        # Path VLM (invariato) — vision + testo via mlx-vlm
                        from mlx_vlm import load
                        from mlx_vlm.utils import load_config
                        try:
                            model, processor = load(model_id)
                            config = load_config(model_id)
                        except Exception:
                            os.environ.pop("HF_HUB_OFFLINE", None)
                            model, processor = load(model_id)
                            config = load_config(model_id)
                    else:
                        # Path text-only via mlx-lm — processor = tokenizer,
                        # config non usato (None).
                        from mlx_lm import load as load_lm
                        try:
                            model, processor = load_lm(model_id)
                        except Exception:
                            os.environ.pop("HF_HUB_OFFLINE", None)
                            model, processor = load_lm(model_id)
                        config = None

                    self._model     = model
                    self._processor = processor
                    self._config    = config
                    self._model_id  = model_id
                    self._loading   = False

                    # Limita la Metal cache a 3 GB — senza limite cresce
                    # senza controllo tra generazioni successive.
                    try:
                        import mlx.core as mx
                        mx.metal.set_cache_limit(3 * 1024 ** 3)
                        peak = mx.metal.get_active_memory() / 1024 ** 3
                        log.info(f"MLX active memory dopo load: {peak:.1f} GB")
                    except Exception:
                        pass

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

        self._executor.submit(_work)

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

    def switch_to(
        self,
        model_id: str,
        backend: str,
        api_key: str = "",
        update_preferred: bool = True,
    ) -> None:
        """Cambia backend/modello. Per MLX ricarica il modello sull'executor.

        update_preferred: se True (switch iniziato dall'utente) aggiorna il
        modello preferito. La vision on-demand usa False per non sovrascrivere
        la scelta dell'utente quando carica temporaneamente MODEL_HEAVY.
        """
        self._backend = backend
        if backend == "openrouter":
            self._openrouter_model = model_id
            self._openrouter_key   = api_key or None
            log.info(f"backend → openrouter, model={model_id}")
            for cb in self.on_ready:
                cb(model_id)
        else:
            self._backend = "mlx"
            if update_preferred:
                self._preferred_id = model_id
            self.load_async(model_id)

    def reload(self) -> None:
        """Ricarica il modello MLX corrente."""
        if self._backend == "mlx" and self._model_id:
            self.load_async(self._model_id)

    def redownload(self) -> None:
        """Cancella il modello MLX dalla cache HF e lo riscarica."""
        if self._backend != "mlx" or not self._model_id:
            return
        model_id = self._model_id

        def _delete_and_reload():
            import shutil
            from pathlib import Path
            hf_home = Path.home() / ".cache" / "huggingface" / "hub"
            slug = "models--" + model_id.replace("/", "--")
            target = hf_home / slug
            if target.exists():
                shutil.rmtree(target)
                log.info(f"cancellata cache: {target}")
            import os
            os.environ.pop("HF_HUB_OFFLINE", None)
            self.load_async(model_id)

        self._executor.submit(_delete_and_reload)

    # ------------------------------------------------------------------
    # Vision on-demand
    # ------------------------------------------------------------------

    @property
    def preferred_id(self) -> str:
        return self._preferred_id

    async def ensure_vision_ready(self, timeout: float = 300.0) -> bool:
        """Assicura che un modello VLM sia caricato per la vision.

        Se il modello corrente è già un VLM pronto, ritorna subito. Altrimenti
        ricarica MODEL_HEAVY on-demand (tradeoff consapevole: ~20-30s di reload)
        e attende che sia pronto. Ritorna True se pronto, False se timeout.

        Il chiamante (vision.py) deve poi ripristinare il modello preferito.
        """
        if self._backend == "mlx" and is_vlm(self._model_id) and self.is_ready:
            return True

        log.info(
            f"vision on-demand: ricarico {MODEL_HEAVY} "
            f"(corrente: {self._model_id})"
        )
        self.switch_to(MODEL_HEAVY, "mlx", update_preferred=False)

        import time
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.is_ready and self._model_id == MODEL_HEAVY:
                log.info(f"vision pronta: {MODEL_HEAVY}")
                return True
            await asyncio.sleep(0.5)

        log.error(f"timeout ({timeout}s) attesa modello vision {MODEL_HEAVY}")
        return False

    async def _stream_openrouter(
        self,
        messages: list[dict],
        max_tokens: int,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Stream via OpenRouter (API OpenAI-compatibile)."""
        import httpx
        model = self._openrouter_model or "openai/gpt-4o-mini"
        key   = self._openrouter_key or ""
        url   = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization":      f"Bearer {key}",
            "Content-Type":       "application/json",
            "HTTP-Referer":       "https://ari.local",
            "X-Title":            "Ari",
        }
        body = {
            "model":       model,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "stream":      True,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", url, headers=headers, json=body) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            obj = json.loads(data)
                            token = obj["choices"][0]["delta"].get("content", "")
                            if token:
                                yield ("chunk", token)
                        except Exception:
                            pass
        except Exception as e:
            log.error(f"errore openrouter: {e}")
            yield ("chunk", f"[errore OpenRouter: {e}]")
        yield ("done", "")

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
        if self._backend == "openrouter":
            async for item in self._stream_openrouter(messages, max_tokens):
                yield item
            return

        if not self.is_ready:
            yield ("chunk", "Sto caricando il modello, un momento...")
            yield ("done", "")
            return

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _generate():
            try:
                vlm = is_vlm(self._model_id)

                # Chat template — usa il tokenizer interno del processor.
                # Per i modelli text-only (mlx-lm) self._processor È già il
                # tokenizer (TokenizerWrapper), che espone apply_chat_template.
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

                # Generatore di token: mlx-vlm per i VLM (con image=None),
                # mlx-lm per i modelli text-only. Il parsing dei tag <think>
                # sottostante è identico per entrambi.
                if vlm:
                    from mlx_vlm import stream_generate
                    token_iter = stream_generate(
                        self._model,
                        self._processor,
                        prompt=prompt,
                        image=None,
                        max_tokens=max_tokens,
                        enable_thinking=thinking,
                    )
                else:
                    from mlx_lm import stream_generate as lm_stream_generate
                    token_iter = lm_stream_generate(
                        self._model,
                        self._processor,
                        prompt=prompt,
                        max_tokens=max_tokens,
                    )

                in_think = False
                think_buf = ""

                for resp in token_iter:
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
                # Libera Metal cache accumulata durante la generazione.
                # Senza questa chiamata i buffer non vengono rilasciati tra una risposta e l'altra.
                try:
                    import mlx.core as mx
                    import gc
                    mx.metal.clear_cache()
                    gc.collect()
                except Exception:
                    pass
                loop.call_soon_threadsafe(queue.put_nowait, ("done", ""))

        self._executor.submit(_generate)

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
            result = generate(
                self._model, self._processor, image_pil, formatted,
                max_tokens=max_tokens, verbose=False,
            ).strip()
            return result
        except Exception as e:
            log.error(f"errore generazione vision: {e}")
            return f"Errore durante l'analisi: {e}"
        finally:
            try:
                import mlx.core as mx
                import gc
                mx.metal.clear_cache()
                gc.collect()
            except Exception:
                pass

    def memory_stats(self) -> dict:
        """Ritorna statistiche memoria MLX correnti (GB)."""
        try:
            import mlx.core as mx
            return {
                "active_gb":   round(mx.metal.get_active_memory()   / 1024 ** 3, 2),
                "peak_gb":     round(mx.metal.get_peak_memory()     / 1024 ** 3, 2),
                "cache_gb":    round(mx.metal.get_cache_memory()    / 1024 ** 3, 2),
            }
        except Exception:
            return {}


engine = LLMEngine()
