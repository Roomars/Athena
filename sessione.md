# Stato Sessione

## Progetto
**Athena** — progetto AI assistant personale locale stile Jarvis per macOS M1 Max.
L'AI si chiama **Ari**. Stack: Swift (UI/notch/voce) + Python (brain/MLX/memoria/skills).

## Lavoro corrente
**FASE 1–7 ✅ completate. FASE 8A ✅ completata. FASE 8B in corso — 3/5 tool completati.**

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

1. **FASE 8B** — ✅ file_processor, ✅ youtube, ✅ send_message | da fare: flight_finder, game_updater
2. **FASE 8C** — browser_control (Playwright), computer_control VLM-driven (ispirazione UI-TARS), code_runner sandbox
3. **FASE 9** — UI Evolution: audio waveform nell'orb, state label, grid dot background

---

## Pattern acquisiti da analisi repo (da integrare)

Cinque repo analizzati come riferimento permanente (salvati in memory):

| Repo | Stelle | Pattern chiave per Ari | Quando |
|---|---|---|---|
| Open Notebook | 33k | Multi-query RAG (5 query in parallelo), source ingestion pipeline, ModelManager (4B vs 14B auto) | Memoria v2 + file_processor FASE 8B |
| claude-code-best | 20k | Skill learning evolutivo (osserva gap → genera skill), goal system multi-turno, forked agent memory | FASE 7 upgrade post 8C |
| JCode | 7.8k | Memory DiGraph (Supersedes/Contradicts), hybrid retrieval BM25+dense recall@0.75, ambient mode | Memoria v2 post FASE 8 |
| Supervision | 44.9k | Object detection agnostic (YOLO+Transformers), ByteTracker, ZoneAnnotator, heatmap | FASE 6 upgrade (screen awareness strutturata) |
| UI-TARS Desktop | 37.2k | GUI automation VLM-driven (screenshot→Gemma4→coordinate→azione), ibrido GUI+DOM | FASE 8C computer_control |

### Integrazioni concrete per fase

**FASE 8B — file_processor:**
- Usare `content-core` (Open Notebook) invece di costruire da zero — supporta 50+ formati
- Pattern ingestion: file → extract → vectorize (async) → auto-summary (Transformation pattern)
- ModelManager: file brevi → Qwen3-4B, file lunghi → Qwen3-14B auto

**FASE 8C — computer_control:**
- Non PyAutoGUI statico con coordinate hardcoded
- Pattern UI-TARS: cattura screenshot (VisionCapture già presente) → Gemma 4 12B "dove si trova X?" → coordinate → click/type
- browser_control: Playwright per DOM + Gemma 4 per visual confirmation (hybrid come UI-TARS)

**FASE 6 upgrade (screen awareness):**
- Aggiungere Supervision sopra VisionCapture per output strutturato
- Pattern: screenshot → YOLO local (MPS/CoreML) → sv.Detections → JSON → Gemma 4 sintesi
- Use case: "quante app aperte", "c'è qualcosa di anomalo", zone counting finestre

**Memoria v2 (post FASE 8, dedicata):**
- Sostituire SQLite facts flat con DiGraph (networkx) — nodi Memory/Tag/Cluster
- Edge types: Supersedes, Contradicts, RelatesTo, DerivedFrom
- Retrieval: embedding cosine + BM25 (rank-bm25) + RRF → recall@5 da 0.0 a 0.75
- Multi-query: 3-5 query parallele dalla domanda utente (Open Notebook pattern)
- Post-retrieval: confidence boost/decay async, gap detection

**Skill learning evolutivo (post FASE 8):**
- Ari osserva i propri fallimenti → accumula in gap store → genera nuova skill autonomamente
- Goal system: "Ari, completa FASE 8B" → goal persistente multi-sessione con token budget

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
26-06-2026 - 00:30

## Changelog
- 14-06-2026 15:23: Sessione progettazione completa — IdeasProject/ creato (16 doc, 34 decisioni), stack MLX confermato, nome AI = Ari, due modalità UI (notch + chat), roadmap 10 fasi definita
- 14-06-2026 16:45: Modalità Desktop (17_desktop_mode.md), analisi 3 repo Jarvis, 10 pattern concreti aggiunti a 15_jarvis_features.md
- 14-06-2026 17:00: FASE 1 completata. FASE 2 avviata con MLX-lm Qwen3-14B (104 tok/s su 4B, 14B scaricato).
- 14-06-2026 23:30: FASE 2 completata. UI: 3 finestre NSPanel indipendenti (Orb/Risposta/Input). CyberEyeView particle ring animato. Fix definitivo testo via AppKit callback diretto. Menu tasto destro, toggle finestre, resize. Pronto per FASE 3.
- 15-06-2026 00:00: FASE 3 ✅ (STT SFSpeechRecognizer, hold-to-talk, auto-send, VAD). FASE 4 ✅ (Skills C/B/A: open_app+alias italiani, wake word opt-in con fix -10877, memoria SQLite+estrazione LLM). FASE 5 ✅ (monitor proattivo: batteria/CPU/RAM/saluti, notifiche osascript). Menu ristrutturato, SettingsWindowController con hotkey personalizzabile.
- 15-06-2026 19:30: FASE 5B ✅ (SnapManager widget magnetici, MemoryPanel, StatsPanel+AnomalyDetector). FASE 6 ✅ (VisionCapture + Gemma 4 12B). FASE 7 ✅ (self-modify: classify→generate→diff→ApprovalBanner→apply→git→restart). Nuove skill: web_fetch, file_ops. ClapWakeManager (doppio battito, Iron Man). TTS smart (no lettura codice). Comandi rapidi stop/basta. Roadmap FASE 8-10 definita da analisi Mark-XL (14 tool, UI evolution, upgrade STT).
- 15-06-2026 23:19: FASE 8A ✅ (safari_control, weather, reminder, mac_settings, desktop_control — 13 tool totali attivi). Bug fix loop vocale (tts_done event-driven). "ferma" aggiunto stop. Constitution aggiornata con sezione CAPACITÀ. Self-modify regex espansa. Analisi UI Mark-XL (palette ciano+arancio, HUD waveform → ispirazione FASE 9).
- 25-06-2026 11:30: Analisi 5 repo di riferimento permanente (Open Notebook, claude-code-best, JCode, Supervision, UI-TARS Desktop). Pattern integrati nella roadmap: computer_control VLM-driven (FASE 8C), file_processor con content-core (8B), screen awareness strutturata Supervision (FASE 6 upgrade), Memoria v2 DiGraph+BM25 (post 8), skill learning evolutivo (post 8).
- 26-06-2026 00:30: FASE 8B avviata — 3 tool completati: file_processor (PDF/CSV/DOCX/immagini/audio), youtube (search+info+transcript), send_message (Messages.app osascript). 16 skill totali attive. Prossima sessione: flight_finder + game_updater → FASE 8B completa.
