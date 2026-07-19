import asyncio
import os
import subprocess
import tempfile
import threading
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
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


# ---------------------------------------------------------------------------
# Interfaccia comune
# ---------------------------------------------------------------------------

class TTSBackend(ABC):
    """Interfaccia comune per tutti i motori di sintesi vocale."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Avvia la sintesi di `text`. Ritorna subito (non-blocking)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Interrompe l'eventuale sintesi in corso."""
        ...


# ---------------------------------------------------------------------------
# Implementazione Apple (say / Federica)
# ---------------------------------------------------------------------------

class _AppleBackend(TTSBackend):
    """Motore Apple TTS tramite subprocess `say`."""

    def __init__(
        self,
        lock: threading.Lock,
        get_proc: Callable[[], "subprocess.Popen[bytes] | None"],
        set_proc: Callable[["subprocess.Popen[bytes] | None"], None],
        fire_done: Callable[[], None],
        get_rate_pct: Callable[[], int],
        get_pitch_pct: Callable[[], int],
    ) -> None:
        # Condividiamo lock e riferimento al processo con TTSEngine
        # per permettere a stop() di terminare qualsiasi processo attivo.
        self._lock          = lock
        self._get_proc      = get_proc
        self._set_proc      = set_proc
        self._fire_done     = fire_done
        self._get_rate_pct  = get_rate_pct
        self._get_pitch_pct = get_pitch_pct

    def speak(self, text: str) -> None:
        def _run() -> None:
            proc = None
            try:
                rate_pct  = self._get_rate_pct()
                pitch_pct = self._get_pitch_pct()
                actual_rate = int(APPLE_RATE * rate_pct / 100)
                speak_text  = text
                if pitch_pct != 100:
                    pbas_val   = 60 + int((pitch_pct - 100) * 0.3)
                    speak_text = f"[[pbas {pbas_val}]] {text}"
                with self._lock:
                    proc = subprocess.Popen(
                        ["say", "-v", APPLE_VOICE, "-r", str(actual_rate), speak_text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._set_proc(proc)
                proc.wait()
            except Exception as e:
                log.error(f"TTS Apple errore: {e}")
            finally:
                with self._lock:
                    if self._get_proc() is proc:
                        self._set_proc(None)
                self._fire_done()

        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        # Delegato a TTSEngine che possiede il lock e il proc
        pass


# ---------------------------------------------------------------------------
# Implementazione Kokoro
# ---------------------------------------------------------------------------

class _KokoroBackend(TTSBackend):
    """Motore Kokoro TTS con coda seriale su executor dedicato.

    La sintesi Kokoro usa MLX internamente. Instradare le chiamate
    attraverso un ThreadPoolExecutor(max_workers=1) separato garantisce:
    - Serializzazione delle sintesi Kokoro tra loro
    - Isolamento in un thread pool distinto da quello di LLMEngine._executor
      (nessun coupling cross-modulo, nessun lock cross-file)

    Il fallback automatico ad Apple in caso di errore runtime è preservato.
    """

    def __init__(
        self,
        pipeline: Any,                  # KPipeline
        apple_backend: _AppleBackend,
        lock: threading.Lock,
        get_proc: Callable[[], "subprocess.Popen[bytes] | None"],
        set_proc: Callable[["subprocess.Popen[bytes] | None"], None],
        fire_done: Callable[[], None],
        get_rate_pct: Callable[[], int],
        get_pitch_pct: Callable[[], int],
    ) -> None:
        self._pipeline      = pipeline
        self._apple         = apple_backend
        self._lock          = lock
        self._get_proc      = get_proc
        self._set_proc      = set_proc
        self._fire_done     = fire_done
        self._get_rate_pct  = get_rate_pct
        self._get_pitch_pct = get_pitch_pct
        # Coda seriale dedicata — max_workers=1 serializza le sintesi Kokoro
        # senza interferire con LLMEngine._executor (ThreadPoolExecutor distinto).
        self._executor      = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kokoro")

    def speak(self, text: str) -> None:
        self._executor.submit(self._run, text)

    def _run(self, text: str) -> None:
        tmp  = None
        proc = None
        try:
            rate_pct = self._get_rate_pct()
            chunks = []
            for _, _, audio in self._pipeline(text, voice="if_sara", speed=rate_pct / 100):
                chunks.append(audio)
            if not chunks:
                return

            full = np.concatenate(chunks)

            pitch_pct = self._get_pitch_pct()
            if pitch_pct != 100:
                from scipy.signal import resample as _resample
                semitones    = (pitch_pct - 100) / 50 * 6
                factor       = 2 ** (semitones / 12)
                original_len = len(full)
                full = _resample(full, int(original_len / factor))
                full = _resample(full, original_len)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = f.name
            sf.write(tmp, full, 24000)

            with self._lock:
                proc = subprocess.Popen(
                    ["afplay", tmp],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._set_proc(proc)
            proc.wait()

        except Exception as e:
            log.error(f"TTS Kokoro errore: {e} — fallback Apple")
            # Fallback ad Apple: garantito anche durante errori runtime Kokoro.
            # _apple.speak() lancia un thread separato che chiamerà _fire_done
            # al termine — non richiamiamo _fire_done qui per evitare doppio fire.
            self._apple.speak(text)
            return
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            with self._lock:
                if self._get_proc() is proc:
                    self._set_proc(None)
            # Solo se non siamo nel ramo fallback (return anticipato sopra)
            # il finally raggiunge questo punto.
            if proc is not None:
                self._fire_done()

    def stop(self) -> None:
        # Delegato a TTSEngine
        pass


# ---------------------------------------------------------------------------
# Wrapper pubblico — firma identica all'originale
# ---------------------------------------------------------------------------

class TTSEngine:
    """Wrapper pubblico con interfaccia identica alla versione pre-refactor.

    Metodi pubblici usati da ws_handler.py:
        speak(text)          — sintetizza testo
        stop()               — interrompe la sintesi in corso
        set_engine(engine)   — seleziona "apple" | "kokoro"
        set_enabled(bool)    — abilita/disabilita TTS globalmente
        set_loop(loop)       — imposta l'event loop asyncio
        set_done_callback(cb)— callback async invocata al termine
    """

    def __init__(self) -> None:
        self._proc:    subprocess.Popen | None = None
        self._lock     = threading.Lock()
        self._loop:    asyncio.AbstractEventLoop | None = None
        self._on_done: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._enabled  = True
        self._engine   = "apple"
        self._pipeline = None          # KPipeline lazy-init

        # Tuning — default 100 = comportamento identico a pre-modifica
        self._rate_pct:  int = 100
        self._pitch_pct: int = 100

        # Coda streaming — usata da enqueue() per riprodurre frasi in sequenza
        # senza tagliarsi a vicenda (a differenza di speak(), che interrompe).
        # _speaking indica se una sintesi è in corso o in coda; _fire_done()
        # (che notifica "tts_done" a Swift e fa ripartire il wake-word) deve
        # scattare SOLO quando la coda si vuota, non ad ogni singola frase.
        self._queue:       list[str] = []
        self._queue_lock = threading.Lock()
        self._speaking   = False

        # Backend attivo — inizializzato dopo set_engine() o al primo speak()
        self._backend: TTSBackend | None = None
        self._apple_backend: _AppleBackend | None = None

        # Inizializza subito il backend Apple (sempre disponibile)
        self._init_apple_backend()

    # ------------------------------------------------------------------
    # Helpers interni condivisi tra backend
    # ------------------------------------------------------------------

    def _get_proc(self) -> "subprocess.Popen[bytes] | None":
        return self._proc

    def _set_proc(self, proc: "subprocess.Popen[bytes] | None") -> None:
        self._proc = proc

    def _get_rate_pct(self) -> int:
        return self._rate_pct

    def _get_pitch_pct(self) -> int:
        return self._pitch_pct

    @property
    def rate_pct(self) -> int:
        return self._rate_pct

    @property
    def pitch_pct(self) -> int:
        return self._pitch_pct

    def _init_apple_backend(self) -> None:
        self._apple_backend = _AppleBackend(
            lock=self._lock,
            get_proc=self._get_proc,
            set_proc=self._set_proc,
            fire_done=self._on_chunk_done,
            get_rate_pct=self._get_rate_pct,
            get_pitch_pct=self._get_pitch_pct,
        )
        self._backend = self._apple_backend

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def set_done_callback(self, cb: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._on_done = cb

    def set_engine(self, engine: str) -> None:
        target = engine if engine in ("apple", "kokoro") else "apple"

        if target == "kokoro":
            if not _KOKORO_AVAILABLE:
                log.warning("Kokoro non installato — fallback Apple")
                target = "apple"
            else:
                if self._pipeline is None:
                    try:
                        self._pipeline = KPipeline(lang_code="i")
                        log.info("Kokoro pipeline inizializzata (IT)")
                    except Exception as e:
                        log.error(f"Kokoro init errore: {e} — fallback Apple")
                        target = "apple"

        self._engine = target

        if self._engine == "kokoro" and self._pipeline is not None:
            # Assicuriamoci che _apple_backend esista prima di passarlo a Kokoro
            assert self._apple_backend is not None
            self._backend = _KokoroBackend(
                pipeline=self._pipeline,
                apple_backend=self._apple_backend,
                lock=self._lock,
                get_proc=self._get_proc,
                set_proc=self._set_proc,
                fire_done=self._on_chunk_done,
                get_rate_pct=self._get_rate_pct,
                get_pitch_pct=self._get_pitch_pct,
            )
        else:
            self._backend = self._apple_backend

        log.info(f"TTS engine: {self._engine}")

    def speak(self, text: str) -> None:
        """Sintetizza `text` immediatamente, interrompendo qualsiasi sintesi
        (e coda) in corso. Comportamento invariato rispetto a pre-streaming."""
        if not self._enabled or not text.strip():
            return
        self.stop()
        with self._queue_lock:
            self._speaking = True
        assert self._backend is not None
        self._backend.speak(text)

    def enqueue(self, text: str) -> None:
        """Accoda `text` per la sintesi, in sequenza con eventuali testi già
        in coda — a differenza di speak(), NON interrompe una sintesi in
        corso. Usato per lo streaming TTS a frasi durante la generazione."""
        if not self._enabled or not text.strip():
            return
        with self._queue_lock:
            if self._speaking:
                self._queue.append(text)
                return
            self._speaking = True
        assert self._backend is not None
        self._backend.speak(text)

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            self._proc = None
        with self._queue_lock:
            self._queue.clear()
            self._speaking = False
        if proc and proc.poll() is None:
            proc.terminate()

    def set_tuning(self, rate_pct: int, pitch_pct: int) -> None:
        """Imposta rate e pitch in percentuale (50-150). 100 = default invariato."""
        self._rate_pct  = max(50, min(150, rate_pct))
        self._pitch_pct = max(50, min(150, pitch_pct))
        log.info(f"TTS tuning: rate={self._rate_pct}% pitch={self._pitch_pct}%")

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.stop()
        log.info(f"TTS {'attivato' if enabled else 'disattivato'}")

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _on_chunk_done(self) -> None:
        """Chiamato dal backend quando UNA sintesi (una entry della coda) è
        terminata. Se c'è altro in coda, avvia il prossimo elemento; solo a
        coda vuota notifica la fine reale (_fire_done → "tts_done" a Swift,
        che fa ripartire il wake-word — deve scattare una sola volta per
        risposta, non ad ogni frase)."""
        with self._queue_lock:
            next_text = self._queue.pop(0) if self._queue else None
            if next_text is None:
                self._speaking = False
        if next_text is not None:
            assert self._backend is not None
            self._backend.speak(next_text)
        else:
            self._fire_done()

    def _fire_done(self) -> None:
        if self._on_done and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._on_done(), self._loop)


tts = TTSEngine()
