import asyncio
import subprocess
import threading
import logging
from collections.abc import Callable, Coroutine
from typing import Any

log = logging.getLogger("tts")

VOICE = "Federica (Premium)"
RATE  = 185


class TTSEngine:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock    = threading.Lock()
        self._loop:   asyncio.AbstractEventLoop | None = None
        self._on_done: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._enabled = True

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Registra il loop asyncio principale per la notifica tts_done."""
        self._loop = loop

    def set_done_callback(self, cb: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """Callback async chiamato quando il TTS termina (naturally o via stop)."""
        self._on_done = cb

    def speak(self, text: str) -> None:
        if not self._enabled or not text.strip():
            return
        self.stop()
        def _run():
            with self._lock:
                try:
                    self._proc = subprocess.Popen(
                        ["say", "-v", VOICE, "-r", str(RATE), text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._proc.wait()
                except Exception as e:
                    log.error(f"TTS errore: {e}")
                finally:
                    self._proc = None
                    self._fire_done()
        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                self._proc = None

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.stop()
        log.info(f"TTS {'attivato' if enabled else 'disattivato'}")

    def _fire_done(self) -> None:
        if self._on_done and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._on_done(), self._loop)


tts = TTSEngine()
