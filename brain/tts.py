import subprocess
import threading
import logging

log = logging.getLogger("tts")

VOICE   = "Federica (Premium)"
RATE    = 185   # parole al minuto (default 175, un po' più veloce)
ENABLED = True  # togglabile via WebSocket


class TTSEngine:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        if not ENABLED or not text.strip():
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
        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                self._proc = None

    def set_enabled(self, enabled: bool) -> None:
        global ENABLED
        ENABLED = enabled
        if not enabled:
            self.stop()
        log.info(f"TTS {'attivato' if enabled else 'disattivato'}")


tts = TTSEngine()
