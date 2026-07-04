import asyncio
import os
import subprocess
import tempfile
import threading
import logging
from collections.abc import Callable, Coroutine
from typing import Any

log = logging.getLogger("tts")

APPLE_VOICE = "Federica (Premium)"
APPLE_RATE  = 185

import numpy as np   # già nel venv, sempre disponibile

try:
    from kokoro import KPipeline
    import soundfile as sf
    _KOKORO_AVAILABLE = True
    log.info("Kokoro disponibile")
except ImportError:
    _KOKORO_AVAILABLE = False
    log.info("Kokoro non installato — usando Apple TTS")


class TTSEngine:
    def __init__(self):
        self._proc:     subprocess.Popen | None = None
        self._lock      = threading.Lock()
        self._loop:     asyncio.AbstractEventLoop | None = None
        self._on_done:  Callable[[], Coroutine[Any, Any, None]] | None = None
        self._enabled   = True
        self._engine    = "apple"          # "apple" | "kokoro"
        self._pipeline  = None             # KPipeline lazy-init

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def set_done_callback(self, cb: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._on_done = cb

    def set_engine(self, engine: str) -> None:
        self._engine = engine if engine in ("apple", "kokoro") else "apple"
        if self._engine == "kokoro":
            if not _KOKORO_AVAILABLE:
                log.warning("Kokoro non installato — fallback Apple")
                self._engine = "apple"
            elif self._pipeline is None:
                try:
                    self._pipeline = KPipeline(lang_code="i")
                    log.info("Kokoro pipeline inizializzata (IT)")
                except Exception as e:
                    log.error(f"Kokoro init errore: {e} — fallback Apple")
                    self._engine = "apple"
        log.info(f"TTS engine: {self._engine}")

    def speak(self, text: str) -> None:
        if not self._enabled or not text.strip():
            return
        self.stop()
        if self._engine == "kokoro" and self._pipeline is not None:
            self._speak_kokoro(text)
        else:
            self._speak_apple(text)

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            self._proc = None
        if proc and proc.poll() is None:
            proc.terminate()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.stop()
        log.info(f"TTS {'attivato' if enabled else 'disattivato'}")

    # MARK: - Apple TTS

    def _speak_apple(self, text: str) -> None:
        def _run():
            proc = None
            try:
                with self._lock:
                    proc = subprocess.Popen(
                        ["say", "-v", APPLE_VOICE, "-r", str(APPLE_RATE), text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._proc = proc
                proc.wait()
            except Exception as e:
                log.error(f"TTS Apple errore: {e}")
            finally:
                with self._lock:
                    if self._proc is proc:
                        self._proc = None
                self._fire_done()
        threading.Thread(target=_run, daemon=True).start()

    # MARK: - Kokoro TTS

    def _speak_kokoro(self, text: str) -> None:
        def _run():
            tmp = None
            proc = None
            try:
                chunks = []
                for _, _, audio in self._pipeline(text, voice="if_sara", speed=1.0):
                    chunks.append(audio)
                if not chunks:
                    return

                full = np.concatenate(chunks)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    tmp = f.name
                sf.write(tmp, full, 24000)

                with self._lock:
                    proc = subprocess.Popen(
                        ["afplay", tmp],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._proc = proc
                proc.wait()

            except Exception as e:
                log.error(f"TTS Kokoro errore: {e} — fallback Apple")
                self._speak_apple(text)
                return
            finally:
                if tmp and os.path.exists(tmp):
                    try: os.unlink(tmp)
                    except OSError: pass
                with self._lock:
                    if self._proc is proc:
                        self._proc = None
                self._fire_done()
        threading.Thread(target=_run, daemon=True).start()

    def _fire_done(self) -> None:
        if self._on_done and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._on_done(), self._loop)


tts = TTSEngine()
