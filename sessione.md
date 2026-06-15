# Stato Sessione

## Progetto
**Athena** — progetto AI assistant personale locale stile Jarvis per macOS M1 Max.
L'AI si chiama **Ari**. Stack: Swift (UI/notch/voce) + Python (brain/MLX/memoria/skills).

## Lavoro corrente
**FASE 1–7 ✅ completate. FASE 8A ✅ completata. Prossima: FASE 8B.**

### FASE 8A — Tool Expansion batch 1 (completata)
- `safari_control`: naviga in Safari via osascript — "vai su X", "apri URL", "ricarica pagina"
- `weather`: meteo real-time via wttr.in — temperatura, condizione, umidità, vento, previsione domani
- `reminder`: crea promemoria in Reminders.app — "ricordami di X"
- `mac_settings`: volume (alza/abbassa/imposta/muta), dark/light mode, sleep, blocca schermo
- `desktop_control`: Dock (nascondi/mostra), Finder, svuota cestino, sfondo desktop

### Bug fix sessione 15-06-2026 sera
- **Loop vocale risolto**: wake manager ora si riavvia solo dopo `tts_done` (event-driven via WebSocket), non in `onFinalResult` — eliminato il loop mic→TTS→mic
- **"ferma" / "ari ferma"** aggiunti ai comandi stop rapidi
- **Ari diceva "non posso"**: aggiunta sezione CAPACITÀ in `constitution/ari.md` con tutti i 13 tool attivi
- **Self-modify regex espansa**: catch di più trigger naturali (aggiungiti, costruisciti, programmati, ecc.)
- **ClapWakeManager**: doppio battito di mani come wake trigger (stile Iron Man), toggle in Impostazioni → Voce
- **TTS smart**: rimuove blocchi di codice prima di parlare, dice "Il codice è nel pannello"

## Fasi completate

| Fase | Stato | Descrizione |
|---|---|---|
| FASE 1 | ✅ | Setup progetto, Swift + Python, WebSocket |
| FASE 2 | ✅ | UI: 3 NSPanel flottanti (Orb/Risposta/Input), CyberEyeView |
| FASE 3 | ✅ | Voce: STT SFSpeechRecognizer, hold-to-talk, VAD, TTS Federica |
| FASE 4A | ✅ | Memoria SQLite: fatti + episodi, estrazione LLM in background |
| FASE 4B | ✅ | Wake word "ehi Ari", WakeWordManager con restart 50s |
| FASE 4C | ✅ | Skills: open_app, web_search, system_info, clipboard |
| FASE 5 | ✅ | Proattività: monitor CPU/RAM/batteria, saluti, notifiche osascript |
| FASE 5B | ✅ | Widget Magnetici (SnapManager), MemoryPanel raw SQLite, StatsPanel real-time |
| FASE 6 | ✅ | Screen awareness: VisionCapture → Gemma 4 12B mlx-vlm |
| FASE 7 | ✅ | Self-modification: classify → generate → diff → ApprovalBanner → apply → git commit → restart |

## Prossime priorità

1. **FASE 8B** — file_processor (PDF/CSV/audio), youtube, send_message via Messages.app, flight_finder, game_updater
2. **FASE 8C** — browser_control (Playwright), computer_control (PyAutoGUI), code_runner sandbox
3. **FASE 9** — UI Evolution: audio waveform nell'orb, state label, grid dot background

### FASE 8 — Tool Expansion (da Mark-XL, 14 nuovi tool)

#### 8A — Solo osascript/API, zero nuove dipendenze
| Tool | Descrizione | Pattern |
|---|---|---|
| `weather` | Meteo in tempo reale via wttr.in (testo, no browser) | HTTP API |
| `reminder` | Crea promemoria in Reminders.app tramite osascript | osascript |
| `mac_settings` | Volume, luminosità, dark mode, WiFi, sleep via osascript | osascript |
| `desktop_control` | Sfondo desktop, Dock, Exposé via osascript | osascript |

#### 8B — Nuove dipendenze medie
| Tool | Descrizione | Dipendenze |
|---|---|---|
| `file_processor` | Legge PDF, CSV, audio, immagini, video | pdfplumber, pandas, whisper, Pillow |
| `youtube` | Cerca video, scarica info, apri/riproduci | yt-dlp |
| `send_message` | Invia messaggi via Messages.app (osascript, no cloud) | osascript |
| `flight_finder` | Cerca voli via web_fetch (Kayak/Google Flights) | web_fetch (già presente) |
| `game_updater` | Info/aggiornamento giochi Steam tramite shell | steamcmd o steam:// protocol |

#### 8C — Permessi avanzati macOS
| Tool | Descrizione | Permessi richiesti |
|---|---|---|
| `browser_control` | Automazione browser completa | Playwright, accessibilità |
| `computer_control` | Mouse, tastiera, click precisi | PyAutoGUI + Accessibilità |
| `code_runner` | Esegue Python/shell in sandbox con timeout | subprocess sandbox |
| `dev_agent` | Genera progetto multi-file completo | self_modify come base |
| `agent_task` | Esegue task autonomi multi-step con verifica | LLM loop interno |

### FASE 9 — UI Evolution (ispirata a Mark-XL + originale Ari)
- **Audio waveform** nell'OrbView quando Ari parla (linea animata ampiezza voce)
- **State label** "ASCOLTANDO / PENSANDO / PARLANDO" come testo nell'orb
- **Orange accent** (#FF6B00) per anomalie/errori negli StatsPanel (già parzialmente presente)
- **Grid dot background** sottile nei pannelli risposta e memoria
- **MetricBar upgrade** per StatsPanel: barre stile cyberpunk con bordo ciano

### FASE 10 — Qualità voce
- STT upgrade: SFSpeechRecognizer → whisper-large via Python in background (più accurato)
- Miglioramento riconoscimento vocale in ambiente rumoroso

## Blocker attivi
Nessuno.

## Ultimo aggiornamento
15-06-2026 - 23:19

## Changelog
- 14-06-2026 15:23: Sessione progettazione completa — IdeasProject/ creato (16 doc, 34 decisioni), stack MLX confermato, nome AI = Ari, due modalità UI (notch + chat), roadmap 10 fasi definita
- 14-06-2026 16:45: Modalità Desktop (17_desktop_mode.md), analisi 3 repo Jarvis, 10 pattern concreti aggiunti a 15_jarvis_features.md
- 14-06-2026 17:00: FASE 1 completata. FASE 2 avviata con MLX-lm Qwen3-14B (104 tok/s su 4B, 14B scaricato).
- 14-06-2026 23:30: FASE 2 completata. UI: 3 finestre NSPanel indipendenti (Orb/Risposta/Input). CyberEyeView particle ring animato. Fix definitivo testo via AppKit callback diretto. Menu tasto destro, toggle finestre, resize. Pronto per FASE 3.
- 15-06-2026 00:00: FASE 3 ✅ (STT SFSpeechRecognizer, hold-to-talk, auto-send, VAD). FASE 4 ✅ (Skills C/B/A: open_app+alias italiani, wake word opt-in con fix -10877, memoria SQLite+estrazione LLM). FASE 5 ✅ (monitor proattivo: batteria/CPU/RAM/saluti, notifiche osascript). Menu ristrutturato, SettingsWindowController con hotkey personalizzabile.
- 15-06-2026 19:30: FASE 5B ✅ (SnapManager widget magnetici, MemoryPanel, StatsPanel+AnomalyDetector). FASE 6 ✅ (VisionCapture + Gemma 4 12B). FASE 7 ✅ (self-modify: classify→generate→diff→ApprovalBanner→apply→git→restart). Nuove skill: web_fetch, file_ops. ClapWakeManager (doppio battito, Iron Man). TTS smart (no lettura codice). Comandi rapidi stop/basta. Roadmap FASE 8-10 definita da analisi Mark-XL (14 tool, UI evolution, upgrade STT).
- 15-06-2026 23:19: FASE 8A ✅ (safari_control, weather, reminder, mac_settings, desktop_control — 13 tool totali attivi). Bug fix loop vocale (tts_done event-driven). "ferma" aggiunto stop. Constitution aggiornata con sezione CAPACITÀ. Self-modify regex espansa. Analisi UI Mark-XL (palette ciano+arancio, HUD waveform → ispirazione FASE 9).
