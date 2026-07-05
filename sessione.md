# Stato Sessione

## Progetto
**Athena** — progetto AI assistant personale locale stile Jarvis per macOS M1 Max.
L'AI si chiama **Ari**. Stack: Swift (UI/notch/voce) + Python (brain/MLX/memoria/skills).

## Lavoro corrente
**Sessione 05-07-2026 (mattina + pomeriggio): completato Settings Avanzate (modello AI), OpenRouter backend, redesign CyberEyeView orb (guscio vitreo + fulmini tapered).**

### FASE 8B + 8C ✅ (completate sessione 26-06-2026 mattina)
- `flight_finder`: cerca voli, deep link Google Flights + Skyscanner, 40+ città IATA, parser date italiano
- `game_updater`: Steam Store API + Steam News API (no key), apri gioco via `steam://rungameid/`, BM25-like search
- `code_runner`: esegue Python/shell in sandbox subprocess, 30s timeout, blocca comandi pericolosi
- `browser_control`: Playwright headed Chromium, azioni navigate/search/fill/click/extract
- `computer_control`: UI-TARS pattern — screencapture → VLM coords → PyAutoGUI click/type
- **21 skill totali attive** (ordinate per priorità in `__init__.py`)

### FASE 9 ✅ UI Evolution (completata sessione 26-06-2026 mattina)
- `CyberEyeView` riscritto: 12 layer (sclera, particleRing 4 armoniche, circuitSegments, irisMicro 48 fibre, irisRays 72, pupil, waveform radiale, specular Purkinje, eyelidArcs)
- Orb panel solido (no trasparenza), cornerRadius layer, dimensione 224×224
- `liveAmp = max(stateAmp, cpuLoad * 1.80)` — onde workload-driven
- Badge stato (IDLE/LISTENING/THINKING/SPEAKING) posizionato nella metà inferiore dell'iride

### FASE 10 ✅ STT Upgrade (completata sessione 26-06-2026 mattina)
- `stt.py` riscritto: mlx-whisper large-v3-turbo, sounddevice InputStream, VAD silence detection thread
- `VoiceManager.swift` semplificato: solo WebSocket signal, zero AVAudioEngine/SFSpeechRecognizer
- `ws_handler.py`: `_stt_start` (hold/VAD) + `_stt_stop` + `_on_stt_result` — Python gestisce LLM direttamente

### Memoria v2 ✅ (completata sessione 26-06-2026 sera)
- `memory_store.py` riscritto: BM25 puro (zero dipendenze), tokenizer underscore-aware, RRF fusion 3 query
- Schema esteso: colonne `tags`, `confidence`, `source`, `created_at`; tabella `relations` (Supersedes/Contradicts/RelatesTo); migrazione automatica su DB esistente
- Auto-tagging: classifica chiavi in "identità", "professione", "tecnologia", "famiglia", ecc.
- Relazione `Supersedes` automatica quando un fatto cambia valore
- `MemoryPanel.swift` riscritto: panel 820×640, due colonne (fatti 62% | episodi 38%), search live, confidence bar, tag verdi, relazioni viola, footer timestamp

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

1. **Widget grafo 3D del brain** — finestra NSPanel con grafo 3D dei nodi memoria (networkx → JSON → WKWebView Three.js force-directed graph)
2. **mlx-embeddings + nomic-embed-text** — dense retrieval reale per Memoria v2 (BM25+dense già preparato in memory_store.py, manca il modello)
3. **Emotional scoring sulla memoria** — `emotional_score` su memory_store.py (neutral/positive/negative/urgent), weighting retrieval

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
05-07-2026 - 10:21

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
- 26-06-2026 22:18: FASE 8B ✅ (flight_finder, game_updater) + FASE 8C ✅ (code_runner, browser_control, computer_control) + FASE 9 ✅ (CyberEyeView 12 layer, orb solido workload-driven) + FASE 10 ✅ (STT mlx-whisper VAD) + Memoria v2 ✅ (BM25+RRF+relations+tags, MemoryPanel 820×640 due colonne). 21 skill attive. Roadmap FASE 1–10 completata.
- 26-06-2026 23:32: Sessione orb JARVIS — CyberEyeView riscritto 3× (HUD anelli → plasma swirls → sfera elettrica con lightning). Versione finale: lightning bolts zigzag+ramificazioni (plusLighter), 28 surface sparks con spike, swirl plasma morbidi, nucleo bianco. Orb panel reso trasparente (nessun rettangolo visibile). Speaker verification: brain/speaker_verifier.py MFCC 120-dim cosine>0.82, integrato in stt.py pre-Whisper, enrollment via WebSocket voice_enroll.
- 27-06-2026: Sessione auto-conoscenza — Memoria v2 upgraded (DiGraph networkx, BM25+TF-IDF+RRF 5-query, contradiction detection, gap detection, confidence decay, LLM episode summary). MemoryPanel v2 Swift (gap section, color-coded relations). FASE 6 upgrade (YOLO+supervision structured screen analysis). Orb WebGL → stella supergigante azzurra Three.js/GLSL + fake bloom + orbital particles GPU-side → implementato in Swift via WKWebView. constitution/ari.md riscritto con self-knowledge completo (21 tool, architettura Swift+Python, procedura self-modify, limitazioni). constitution/local_ai_ecosystem.md creato (analisi awesome-local-ai: upgrade prioritizzati per retrieval semantico, TTS, modelli).
- 03-07-2026 22:56: Bugfix critici (TTS deadlock lock/proc.wait separati, SAVE_TO strippato prima di TTS, @app.on_event → lifespan asynccontextmanager). Migrazione modello primario Qwen3-14B → Gemma 4 31B-it via mlx-vlm (testo+vision in un modello, -7GB RAM). CyberEyeView: lerp RGB per transizioni fluide (0.55s), LISTENING state con radar rings, event pulse memory_save/contradiction. Verifica FASE 8B: flight_finder e game_updater confermati operativi su API reali. Analisi Khoj (hybrid search + job scheduler) e ComfyUI (image_gen via REST) — pattern aggiunti a roadmap.
- 05-07-2026 09:44: Fix GPU stream error "no stream gpu 3" (root cause: MLX Metal streams thread-local, fix: ThreadPoolExecutor(max_workers=1) in llm.py per caricamento+generazione sullo stesso thread). Fix orb offline (waitForHealth 30→60 tentativi, WebSocketManager.connect() cancella task precedente). Fix notch mode switch (orderFrontRegardless). YOLO monkeypatch torch.backends.mps.is_available=False. Sistema approvazione 3 livelli completo (ApprovalBanner Nega/Consenti/Consenti sempre, ws_handler approval_future, Swift handler). DynamicNotchKit SPM + AriNotchNotifier. Skill Obsidian/Calendar/Mail. Heartbeat proattivo. Cognitive 4-layer: ActionExecutor (approval+retry centralizzati, LLM non esegue azioni direttamente). Spark system: SparkStore SQLite (~/.ari/sparks.db) per cooldown e rate limit persistenti. Analisi moeru-ai/airi (41k⭐): VAD Silero, Beat Sync fisico, 4-layer Minecraft agent, expression blend modes, wLipSync.
- 05-07-2026 10:21: Settings Avanzate — sezione MODELLO AI completa: status dot Combine live, segmented backend Locale MLX/OpenRouter, NSPopUpButton 5 preset MLX, campi model ID + API key OpenRouter, pulsanti Cambia/Riavvia/Riscarica, wrapScrollable() per contenuto scrollabile. llm.py: switch_to(), reload(), redownload() (cancella cache HF), _stream_openrouter() httpx async, routing stream() per backend. ws_handler.py: handler model_switch/model_reload/model_redownload. CyberEyeView redesign: layer order (lightning PRIMA del guscio → fulmini intrappolati), drawVitreousShell() con Fresnel limb darkening + speculare primario + caustic, drawSphereBody() gradiente non-lineare 6 stop, drawBolt() tapered (radice 2.8pt → punta 0.6pt), jitter scalato con progress (0 al centro → max alla punta), ramo secondario tapered più sottile.
