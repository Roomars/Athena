# Athena — Operatività

## First Run — primo avvio

La prima volta che Athena parte, deve fare setup prima di essere usabile.
Un wizard minimale (finestra separata dall'orb) guida Roby:

```
Step 1 — Verifica dipendenze
  ✅ Ollama installato?        → se no: link download
  ✅ Qwen3 14B scaricato?     → se no: avvia download (9GB, mostra progresso)
  ✅ Porcupine key valida?    → inserire API key gratuita

Step 2 — Permessi macOS (richiesti una sola volta)
  → Microfono
  → Accessibilità (per AppleScript e mac_control)
  → Cartelle (per file_ops)
  → Notifiche

Step 3 — Configurazione base
  → Vault AthenaInput path (default: ~/Google Drive/AthenaInput)
  → Home Assistant URL + token (opzionale, saltabile)
  → Hotkey globale (default: Cmd+Shift+A)

Step 4 — Test voce
  → Ascolta "Ciao Athena" e verifica che Athena risponda
  → Se fallisce: troubleshooting inline

Done → orb appare, wizard scompare, non viene più mostrato.
```

---

## Configurazione — dove vivono le impostazioni

**File:** `~/Library/Application Support/Athena/settings.json`

Gestito dalla Swift app. Il Python daemon lo legge all'avvio.

```json
{
  "version": 1,
  "hotkey": "cmd+shift+a",
  "wake_word_enabled": true,
  "orb_position": "bottom-right",
  "orb_size": 80,
  "silent_mode_schedule": {
    "enabled": false,
    "from": "23:00",
    "to": "07:00"
  },
  "vault_input_path": "~/Library/CloudStorage/GoogleDrive/AthenaInput",
  "vault_local_path": "~/.athena/vault",
  "llm_primary": "qwen3:14b",
  "llm_heavy": "qwen2.5:32b",
  "nvidia_fallback_enabled": false,
  "tts_voice": "Federica (Premium)",
  "home_assistant": {
    "url": "",
    "token": ""
  },
  "setup_completed": true
}
```

**Aggiornamento settings:** solo via UI Settings panel in Swift.
Il daemon Python legge il file al boot e ad ogni modifica (watchdog).
Non hardcodare mai valori di configurazione nel codice.

---

## Hotkey globale (CGEvent tap)

Usa CGEvent tap a livello OS — funziona ovunque, anche su lock screen.
Richiede permesso Accessibility (già nel first run wizard).
Pattern da `arinltte/LUCE`.

```swift
let tap = CGEvent.tapCreate(
    tap: .cgSessionEventTap,
    place: .headInsertEventTap,
    options: .defaultTap,
    eventsOfInterest: CGEventMask(1 << CGEventType.keyDown.rawValue),
    callback: { _, _, event, _ in
        if isTargetHotkey(event) { toggleAri(); return nil }
        return Unmanaged.passUnretained(event)
    },
    userInfo: nil
)
```

---

## Auto-start al login

**Meccanismo:** LaunchAgent plist — il sistema macOS standard per daemon utente.

```xml
<!-- ~/Library/LaunchAgents/com.roby.athena.plist -->
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.roby.athena</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Applications/Athena.app/Contents/MacOS/Athena</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
```

L'app Swift e' registrata come Login Item tramite SwiftUI `SMAppService` (API moderna macOS 13+).
Il Python daemon viene lanciato dalla Swift app come subprocess — non serve un LaunchAgent separato per Python.

**Startup sequence:**
```
Login macOS
  → Swift app si avvia (SMAppService)
  → Swift lancia Python daemon subprocess
  → Python daemon avvia FastAPI su porta 8765
  → Swift verifica /health ogni 2s per 10s
  → Se OK: orb appare in idle
  → Se KO dopo 10s: notifica errore con link diagnostica
```

---

## Privacy Mode — silenzio istantaneo

**Attivazione:** click sull'icona menu bar → "Pausa" (o hotkey dedicata `Cmd+Shift+P`)

**Cosa succede in Privacy Mode:**
- Wake word: disabilitato (silenzio assoluto sul microfono)
- Hotkey globale: disabilitata
- TTS output: disabilitato
- Microfono: rilasciato completamente (AVAudioEngine stopped)
- Orb: scompare dallo schermo
- Icona menu bar: diventa grigia con simbolo pausa

**Cosa rimane attivo:**
- Python daemon: gira in background (memoria, tasks in corso)
- WebSocket: connesso
- Background tasks già avviati: continuano

**Riattivazione:** click sull'icona grigia → Athena riprende.
Alternatively: hotkey `Cmd+Shift+P` di nuovo.

**Auto-pausa:** se Athena rileva una chiamata attiva in FaceTime o Telefono → Privacy Mode automatica.
Quando la chiamata termina → Athena chiede "Riprendo?" (testo, non voce).

---

## Background Tasks

Quando Athena esegue un task lungo (studio documenti, web research, compilazione):

**Comportamento orb:**
- Orb in stato "elaborazione" (rotazione particelle lenta)
- Icona menu bar: indicatore di attività animato
- L'utente può continuare a parlare ad Athena (multi-task)

**Notifica al completamento:**
- Notifica macOS nativa
- Orb torna a idle con breve flash di conferma
- Athena dice (o scrive): "[task] completato — [risultato sintetico]"

**Cancellazione:**
- "Athena, fermati" → task corrente annullato
- O click su "Stop" nell'orb durante elaborazione

**Limite:** max 1 background task pesante alla volta. Se ne arriva un secondo, Athena avvisa e mette in coda.

---

## Context Window Management

La working memory e' un array sliding window.

**Limite pratico:** Qwen3 14B ha context 32k token (~24k parole).
Athena mantiene gli ultimi 20 messaggi come minimo. Se si avvicina al limite:

```
Token count > 80% del context window
  → Athena comprime i messaggi più vecchi in un sommario
  → Il sommario sostituisce i messaggi originali nel contesto
  → I messaggi originali vanno in episodic memory
  → Conversazione continua senza interruzione
```

L'utente non vede questa operazione — avviene in background trasparentemente.

---

## Primo download modelli

Al primo avvio, se i modelli non sono presenti:

```
Qwen3 14B: ~9GB  — scaricato in background, mostra progress bar
whisper large-v3-turbo: ~1.5GB — scaricato in background
nomic-embed-text: ~274MB — scaricato silenziosamente
```

Athena e' usabile in modalità testuale limitata durante il download.
Avvisa quando ogni modello e' pronto.
Il 32B (21GB) viene scaricato solo su richiesta esplicita ("carica il modello pesante").
