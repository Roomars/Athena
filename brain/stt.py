"""
STT engine — mlx-whisper su Apple Silicon.
Supporta due modalità:
  - hold-to-talk: start() → stop_and_transcribe()
  - VAD:          start_vad(on_result) → si ferma automaticamente sul silenzio
"""
import threading
import logging
import numpy as np

log = logging.getLogger("stt")

SAMPLE_RATE  = 16000
LANGUAGE     = "it"
# large-v3-turbo: ~809MB, accuratezza vicina a large-v3 ma 3× più veloce
MODEL        = "mlx-community/whisper-large-v3-turbo"

SPEECH_THRESH  = 0.022   # RMS minima per considerare "parlato"
SILENCE_THRESH = 0.012   # RMS sotto cui è silenzio
INITIAL_WAIT   = 8.0     # secondi max prima che inizi a parlare (VAD)
MAX_DURATION   = 60.0    # durata max registrazione
SILENCE_SEC    = 2.2     # secondi di silenzio continuo per fermarsi


class STTEngine:
    def __init__(self):
        self._recording    = False
        self._frames: list[np.ndarray] = []
        self._stream       = None
        self._lock         = threading.Lock()
        self._vad_thread: threading.Thread | None = None
        self.is_ready      = False

    # ── Boot (caricamento lazy in background) ────────────────────────────────

    def load_async(self) -> None:
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self) -> None:
        try:
            import mlx_whisper
            silence = np.zeros(SAMPLE_RATE // 2, dtype=np.float32)
            mlx_whisper.transcribe(silence, path_or_hf_repo=MODEL,
                                   language=LANGUAGE, verbose=False)
            self.is_ready = True
            log.info(f"STT pronto — {MODEL}")
        except Exception as e:
            log.error(f"STT caricamento fallito: {e}")

    # ── Hold-to-talk ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """Avvia la registrazione (stop manuale via stop_and_transcribe)."""
        with self._lock:
            if self._recording:
                return
            self._frames.clear()
            self._recording = True

        try:
            import sounddevice as sd
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            log.info("STT: registrazione avviata (hold-to-talk)")
        except Exception as e:
            log.error(f"STT start errore: {e}")
            with self._lock:
                self._recording = False

    # ── VAD (wake word) ───────────────────────────────────────────────────────

    def start_vad(self, on_result, silence_sec: float = SILENCE_SEC,
                  max_sec: float = MAX_DURATION) -> None:
        """Avvia registrazione con VAD — si ferma automaticamente sul silenzio."""
        with self._lock:
            if self._recording:
                return
            self._frames.clear()
            self._recording = True

        try:
            import sounddevice as sd
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            log.info("STT: registrazione avviata (VAD)")
        except Exception as e:
            log.error(f"STT VAD start errore: {e}")
            with self._lock:
                self._recording = False
            on_result("")
            return

        self._vad_thread = threading.Thread(
            target=self._vad_loop,
            args=(on_result, silence_sec, max_sec),
            daemon=True,
        )
        self._vad_thread.start()

    def _vad_loop(self, on_result, silence_sec: float, max_sec: float) -> None:
        import time
        start_time          = time.time()
        speech_detected     = False
        silent_since: float | None = None
        check_samples       = int(SAMPLE_RATE * 0.30)   # finestra 300ms

        while self._recording:
            time.sleep(0.08)
            elapsed = time.time() - start_time

            # Safety: timeout massimo
            if elapsed > max_sec:
                log.info("STT VAD: timeout massimo raggiunto")
                break

            # Timeout attesa prima parola: se non parla entro INITIAL_WAIT → annulla
            if not speech_detected and elapsed > INITIAL_WAIT:
                log.info("STT VAD: nessun parlato rilevato entro timeout iniziale")
                with self._lock:
                    self._recording = False
                self._stop_stream()
                on_result("")
                return

            if not self._frames:
                continue

            recent = np.concatenate(self._frames, axis=0).flatten()
            if len(recent) < check_samples:
                continue
            rms = float(np.sqrt(np.mean(recent[-check_samples:] ** 2)))

            if not speech_detected:
                if rms > SPEECH_THRESH:
                    speech_detected = True
                    log.info("STT VAD: parlato rilevato")
            else:
                if rms < SILENCE_THRESH:
                    if silent_since is None:
                        silent_since = time.time()
                    elif time.time() - silent_since >= silence_sec:
                        log.info(f"STT VAD: silenzio ({silence_sec}s) — stop")
                        break
                else:
                    silent_since = None

        if self._recording:
            text = self.stop_and_transcribe()
            on_result(text)

    # ── Trascrizione ─────────────────────────────────────────────────────────

    def stop_and_transcribe(self) -> str:
        """Ferma la registrazione e trascrive con Whisper. Thread-safe."""
        with self._lock:
            if not self._recording and not self._frames:
                return ""
            self._recording = False

        self._stop_stream()

        if not self._frames:
            return ""

        try:
            import mlx_whisper
            audio = np.concatenate(self._frames, axis=0).flatten()
            self._frames.clear()

            # Speaker verification — rigetta audio non di Roby
            from .speaker_verifier import verifier
            if not verifier.verify(audio, SAMPLE_RATE):
                log.info("STT: voce non riconosciuta — registrazione scartata")
                return ""

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

    def _stop_stream(self) -> None:
        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        except Exception as e:
            log.warning(f"STT stop stream: {e}")

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if self._recording:
            self._frames.append(indata.copy())

    @property
    def is_recording(self) -> bool:
        return self._recording


stt = STTEngine()
