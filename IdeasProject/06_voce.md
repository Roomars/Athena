# Athena — Pipeline Voce

## Flusso completo

```
MICROFONO
    ↓
[Swift] AVAudioEngine — cattura audio continuo
    ↓
[Swift] Wake word detector — "Ehi Athena"
    oppure Hotkey globale
    ↓
[Swift] Registra utterance (fino a silenzio ~1.5s)
    ↓
[Swift] whisper.cpp — trascrizione in italiano
    ↓
[WebSocket] Invia testo a Python
    ↓
[Python] Elaborazione + risposta
    ↓
[WebSocket] Invia testo risposta a Swift
    ↓
[Swift] Apple TTS (it-IT) — legge la risposta
    oppure [Solo testo] modalità silenziosa
```

---

## STT — whisper.cpp

**Modello:** large-v3-turbo
- Velocità: ~7-10x realtime su M1 Max (Metal)
- Qualità italiano: eccellente
- RAM: ~1.5GB
- Integrazione Swift: via xcframework o subprocess

**Parametri ottimali per conversazione:**
```
language = "it"
task = "transcribe"
beam_size = 5
vad_filter = true    # silenzio → stop automatico
initial_prompt = "Stai parlando con Athena, assistente AI personale."
```

**Alternativa se whisper.cpp è complesso da integrare in Swift:**
Subprocess Python con `whisper` package — leggermente più lento ma più semplice.
Valutare al momento dell'implementazione.

---

## Wake word

**Opzione A — Porcupine (Picovoice):**
- Free tier: 3 wake words custom
- Libreria iOS/macOS nativa
- Latenza: <100ms
- "Hey Athena" custom model trainabile

**Opzione B — Custom leggero:**
- Tiny Whisper (39MB) sempre in ascolto su chunk da 1s
- Controlla se trascrizione contiene "athena"
- Più pesante ma zero dipendenze esterne

**Raccomandazione:** Porcupine per la prima versione (ha SDK Swift, gratuito).
Se diventa un vincolo di licenza, switch a opzione B.

---

## TTS — Opzioni disponibili

### Opzione 1 — Apple TTS nativa (default v1)
**Voice:** Federica (Premium) it-IT
**Vantaggi:** zero latenza, zero dipendenze, streaming word-by-word
**API Swift:**
```swift
let utterance = AVSpeechUtterance(string: text)
utterance.voice = AVSpeechSynthesisVoice(identifier: "com.apple.voice.premium.it-IT.Federica")
utterance.rate = 0.52
synthesizer.speak(utterance)
```

### Opzione 2 — Kokoro TTS (upgrade qualità)
Modello open-source (@hexgrad/kokoro-82M), 82M parametri, offline totale.
Pause matematicamente precise, override fonetici IPA, qualità superiore a Piper.
Architettura: Python backend FastAPI (identica al nostro stack) → Swift chiama via HTTP.

**Riferimento implementazione:** https://github.com/arinltte/KokoroMac
- Stesso pattern Swift+Python subprocess di Ari
- Già testato su Apple Silicon
- Richiede download modello una tantum (~300MB)

**Voce italiana Kokoro:** verificare disponibilità modello it-IT.
Se non disponibile in italiano → manteniamo Apple TTS come default.

### Opzione 3 — Piper
Voce custom italiana, controllabile, già installato in `/piper/`.
Più leggero di Kokoro ma qualità inferiore.

### Decisione
- **FASE 1-6:** Apple TTS nativa (Federica Premium) — zero setup
- **FASE 10:** Valutare Kokoro se voce italiana disponibile e qualità superiore
- **Piper:** terza scelta, solo se le prime due non soddisfano

---

## Modalità silenziosa

Attivabile con comando ("modalità silenziosa") o automaticamente in orario notturno (configurabile).
In modalità silenziosa:
- STT voce: disabilitato (solo input testo)
- TTS: disabilitato
- Risposte: mostrate solo nell'orb come testo
- Wake word: disabilitato
- Hotkey: ancora attiva

---

## Orb sincronizzato con voce

Durante TTS output:
- Athena analizza ampiezza audio in real-time
- Invia a Swift i valori per animare l'orb in sincronia
- L'orb "parla" visivamente mentre Athena parla

```
Python: streaming token TTS → analisi audio →
Swift: { "type": "audio_amplitude", "value": 0.73 } →
Orb: animation frame sincronizzato
```

---

## Hotkey globale

Configurabile in settings. Default suggerito: `Cmd+Shift+A`
(Cmd+Space è occupato da Spotlight, doppio Cmd+Space è più lento)

In alternativa: tasto dedicato o Magic Keyboard shortcut.
