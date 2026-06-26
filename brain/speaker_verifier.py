"""
Speaker verification basata su MFCC + cosine similarity.
Zero dipendenze extra — usa librosa (già presente per whisper).

Enrollment: python -m brain.speaker_verifier --enroll
Runtime:    verifier.verify(audio_np, sr=16000) → bool
"""
import logging
import numpy as np
from pathlib import Path

try:
    import librosa
    _HAS_LIBROSA = True
except ImportError:
    _HAS_LIBROSA = False

PROFILE_PATH = Path(__file__).parent.parent / "data" / "voice_profile.npz"
SAMPLE_RATE  = 16000
THRESHOLD    = 0.82   # soglia cosine similarity (abbassare se troppo restrittivo)
ENROLL_SEC   = 8      # secondi di registrazione per enrollment

log = logging.getLogger("speaker_verifier")


def _extract(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """MFCC (40 coeff) + delta + delta2 → vettore 120-dim."""
    if not _HAS_LIBROSA:
        raise RuntimeError("librosa non disponibile")
    a = audio.astype(np.float32)
    if a.max() > 1.0:
        a = a / 32768.0
    mfcc   = librosa.feature.mfcc(y=a, sr=sr, n_mfcc=40)
    d1     = librosa.feature.delta(mfcc)
    d2     = librosa.feature.delta(mfcc, order=2)
    return np.concatenate([mfcc, d1, d2], axis=0).mean(axis=1)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


class SpeakerVerifier:
    def __init__(self):
        self._profile: np.ndarray | None = None
        self._enabled: bool = True
        self._load()

    def _load(self) -> None:
        if PROFILE_PATH.exists():
            self._profile = np.load(str(PROFILE_PATH))["profile"]
            log.info("profilo vocale caricato")

    # ── Enrollment ────────────────────────────────────────────────────────────

    def enroll(self, audio: np.ndarray, sr: int = SAMPLE_RATE) -> str:
        """Salva il profilo dalla registrazione fornita. Ritorna messaggio di conferma."""
        try:
            self._profile = _extract(audio, sr)
            PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            np.savez(str(PROFILE_PATH), profile=self._profile)
            log.info("profilo vocale salvato")
            return "Profilo vocale registrato. D'ora in poi rispondo solo alla tua voce."
        except Exception as e:
            log.error(f"enroll error: {e}")
            return f"Errore durante la registrazione del profilo: {e}"

    def clear(self) -> None:
        self._profile = None
        if PROFILE_PATH.exists():
            PROFILE_PATH.unlink()
        log.info("profilo vocale rimosso")

    # ── Verification ──────────────────────────────────────────────────────────

    def verify(self, audio: np.ndarray, sr: int = SAMPLE_RATE) -> bool:
        """True se la voce appartiene all'utente registrato (o se nessun profilo è presente)."""
        if not self._enabled or self._profile is None or not _HAS_LIBROSA:
            return True
        try:
            features = _extract(audio, sr)
            sim = _cosine(self._profile, features)
            log.debug(f"speaker similarity={sim:.3f} threshold={THRESHOLD}")
            return sim >= THRESHOLD
        except Exception as e:
            log.debug(f"verify skipped: {e}")
            return True  # in caso di errore, non bloccare

    @property
    def has_profile(self) -> bool:
        return self._profile is not None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, v: bool) -> None:
        self._enabled = v


verifier = SpeakerVerifier()


# ── CLI enrollment ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sounddevice as sd
    print(f"Registrazione {ENROLL_SEC}s in corso... parla normalmente.")
    audio = sd.rec(int(ENROLL_SEC * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    msg = verifier.enroll(audio.flatten(), SAMPLE_RATE)
    print(msg)
