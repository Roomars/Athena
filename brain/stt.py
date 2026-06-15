import threading
import logging
import numpy as np

log = logging.getLogger("stt")

SAMPLE_RATE = 16000
MODEL       = "mlx-community/whisper-small-mlx"
LANGUAGE    = "it"


class STTEngine:
    def __init__(self):
        self._recording  = False
        self._frames: list[np.ndarray] = []
        self._stream     = None
        self._lock       = threading.Lock()
        self.is_ready    = False

    # ── Precaricamento modello (background, al boot) ─────────────────────

    def load_async(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            import mlx_whisper
            # warm-up con silenzio: carica pesi e compila il grafo
            silence = np.zeros(SAMPLE_RATE // 2, dtype=np.float32)
            mlx_whisper.transcribe(silence, path_or_hf_repo=MODEL,
                                   language=LANGUAGE, verbose=False)
            self.is_ready = True
            log.info(f"STT pronto — {MODEL}")
        except Exception as e:
            log.error(f"STT caricamento fallito: {e}")

    # ── Registrazione ────────────────────────────────────────────────────

    def start(self) -> None:
        if self._recording:
            return
        try:
            import sounddevice as sd
            self._frames = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            log.info("STT: registrazione avviata")
        except Exception as e:
            log.error(f"STT start errore: {e}")
            self._recording = False

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if self._recording:
            self._frames.append(indata.copy())

    def stop_and_transcribe(self) -> str:
        """Ferma la registrazione e restituisce il testo trascritto."""
        self._recording = False
        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        except Exception as e:
            log.error(f"STT stop errore: {e}")

        if not self._frames:
            return ""

        try:
            import mlx_whisper
            audio = np.concatenate(self._frames, axis=0).flatten()
            log.info(f"STT: trascrizione {len(audio)/SAMPLE_RATE:.1f}s di audio...")
            result = mlx_whisper.transcribe(
                audio,
                path_or_hf_repo=MODEL,
                language=LANGUAGE,
                verbose=False,
            )
            text = result.get("text", "").strip()
            log.info(f"STT: '{text}'")
            return text
        except Exception as e:
            log.error(f"STT trascrizione errore: {e}")
            return ""


stt = STTEngine()
