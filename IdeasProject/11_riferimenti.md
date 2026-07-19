# Athena — Riferimenti Esterni e Idee da Copiare

## Repository principale

| Risorsa | URL | Note |
|---|---|---|
| **Athena (Roomars)** | https://github.com/Roomars/Athena | Repo ufficiale del progetto |

---

## LLM e Inference

| Risorsa | URL | Cosa ci trovi |
|---|---|---|
| **MLX-lm** | https://github.com/ml-explore/mlx-lm | LLM inference Apple Silicon — stack primario |
| **MLX-vlm** | https://github.com/ml-explore/mlx-vlm | Vision LLM per screen awareness e immagini |
| MLX Community (HF) | https://huggingface.co/mlx-community | Modelli pre-quantizzati per MLX |
| Qwen3 14B MLX | `mlx_lm.generate --model mlx-community/Qwen3-14B-4bit` | Modello veloce primario |
| Qwen2.5 32B MLX | `mlx_lm.generate --model mlx-community/Qwen2.5-32B-4bit` | Modello potente |
| NVIDIA NIM | https://build.nvidia.com | LLM cloud gratuito fallback (opt-in) |
| nomic-embed-text MLX | https://huggingface.co/mlx-community/nomic-embed-text-v1.5 | Embedding locale |

---

## STT — Speech to Text

| Risorsa | URL | Note |
|---|---|---|
| whisper.cpp | https://github.com/ggerganov/whisper.cpp | C++ port di Whisper, Metal nativo |
| whisper.cpp Swift | https://github.com/ggerganov/whisper.cpp/tree/master/examples/whisper.swiftui | Esempio Swift per xcframework |
| mlx-whisper | https://github.com/ml-explore/mlx-examples/tree/main/whisper | Alternativa MLX per Apple Silicon |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper | Python wrapper, ma lento su Mac senza CUDA |

---

## TTS — Text to Speech

| Risorsa | URL | Note |
|---|---|---|
| Apple AVSpeechSynthesizer | Docs Apple | TTS nativa macOS, voce italiana premium |
| Piper | https://github.com/rhasspy/piper | TTS locale, voce custom, gia' installato |
| Kokoro TTS | https://github.com/hexgrad/kokoro | TTS open-source, qualita' alta, leggero |
| Voci italiane Piper | https://github.com/rhasspy/piper/blob/master/VOICES.md | Elenco voci disponibili it-IT |

---

## Wake Word

| Risorsa | URL | Note |
|---|---|---|
| Porcupine SDK | https://picovoice.ai/platform/porcupine/ | Wake word SDK, free tier, iOS/macOS |
| Porcupine Swift | https://github.com/Picovoice/porcupine | SDK Swift ufficiale |
| Porcupine Console | https://console.picovoice.ai | Crea wake word custom "Athena" |
| openWakeWord | https://github.com/dscripka/openWakeWord | Alternativa open-source |

---

## Memory e Vector DB

| Risorsa | URL | Note |
|---|---|---|
| ChromaDB | https://www.trychroma.com | Vector DB embedded, Python |
| LanceDB | https://lancedb.github.io/lancedb/ | Alternativa piu' veloce per grandi vault |
| Obsidian | https://obsidian.md | Knowledge base con grafo |
| Graphify | — | Visualizzazione grafo Obsidian (da rivalutare) |

---

## Interfaccia macOS

| Risorsa | URL | Note |
|---|---|---|
| MenuBarExtra SwiftUI | https://developer.apple.com/documentation/swiftui/menubarextra | Menu bar nativa macOS 13+ |
| Metal shader tutorial | https://metalbyexample.com | Base per shader orb |
| NSPanel non-activating | Apple Docs | Finestra flottante che non ruba focus |
| Sindre Sorhus hot corners | https://github.com/sindresorhus/Sindre-s-Mac-App | Riferimento menu bar app Swift |

---

## Progetti di riferimento (da analizzare per ispirazione)

### Progetti simili open-source

| Progetto | URL | Stelle | Cosa studiare |
|---|---|---|---|
| **arinltte/ari** | https://github.com/arinltte/ari | 26 | Swift + MLX-lm menu bar, Python venv self-contained, streaming |
| **arinltte/KokoroMac** | https://github.com/arinltte/KokoroMac | — | Kokoro TTS Swift+Python FastAPI, blueprint architettura |
| **arinltte/LUCE** | https://github.com/arinltte/LUCE | 43 | CGEvent tap hotkey sistema, resilience gates atexit+deinit |
| **arinltte/stack** | https://github.com/arinltte/stack | 1 | Codebase→Markdown per RAG, binary filtering intelligente |
| **arinltte/latte** | https://github.com/arinltte/latte | 253 | Menu bar + yt-dlp subprocess, batch download pattern |
| **arinltte/Balance-Separator** | https://github.com/arinltte/Balance-Separator | 1 | P2P UDP+TCP sync multi-device, integer arithmetic discipline |
| **Boring Notch** | https://github.com/TheBoredTeam/boring.notch | — | Notch WindowManager + MouseTracker pattern |
| **Atoll** | https://github.com/Ebullioscopic/Atoll | — | Parallax hover, command surface nel notch |
| **OpenClaw** | https://github.com/openclaw/openclaw | 145k | Skill format, permessi TCC macOS, 162 skill templates |
| **Odysseus** | https://github.com/pewdiepie-archdaemon/odysseus | 70k | Backend FastAPI, ChromaDB integration, email/calendar skills |

### Cosa rubiamo — dettaglio per repo

**arinltte/ari:**
- Pattern Swift menu bar app + Python venv in `~/.ari/`
- HTTP su porta 8080 (noi: WebSocket 8765, ma pattern simile)
- MLX-lm inference integrazione

**arinltte/KokoroMac:**
- Kokoro TTS: pausa matematicamente precise, override fonetici IPA, 100% offline
- Blueprint Swift→Python subprocess per TTS (identico al nostro)
- Alternativa a Apple TTS quando si vuole voce più naturale

**arinltte/LUCE:**
- `CGEventTap` per hotkey globale a livello OS (funziona anche su lock screen)
- Pattern resilienza: `atexit` handler + `deinit` garantiscono cleanup anche in caso di crash
- Brightness safeguard: non mostrare UI sensibile se luminosità < 20%

**arinltte/stack:**
- Algoritmo binary filtering: scarta `.o`, `.pyc`, `.swiftmodule`, `node_modules/`
- Utile quando Ari legge il proprio codebase per RAG e self-modification
- Drag-drop cartelle → Markdown con syntax highlighting

**arinltte/Balance-Separator:**
- P2P discovery: UDP broadcast per trovare device in LAN + TCP per sync stato
- Per Ari: sync memoria/settings tra Mac di casa e Mac/Windows al lavoro, zero server
- Fernet encryption per payloads in transit (anche su LAN privata)

**Boring Notch:**
- `WindowManager.swift` — posizionamento NSPanel nel notch
- `MouseTracker.swift` — proximity detection via NSTrackingArea
- Riferimento principale per FASE 1 notch implementation

**Odysseus:**
- Struttura backend FastAPI: `core/`, `routes/`, `services/`
- ChromaDB + embedding integration
- Skills: email (IMAP/SMTP), calendar (CalDAV), notes, tasks

### Jarvis open-source analizzati

| Progetto | URL | Giudizio | Cosa studiare |
|---|---|---|---|
| **ONEPUNCHMAN411/Jarvis** | https://github.com/ONEPUNCHMAN411/Jarvis | Ottimo — più vicino ad Ari | Strategy memory, ScreenWatcher self-throttle, anti-pattern enforcement, safety timer, argument normalization |
| **open-jarvis/OpenJarvis** | https://github.com/open-jarvis/OpenJarvis | Eccellente per idee architetturali | Complexity router, skill overlay few-shot, loop guard, permission store, morning digest format |
| **SreejanPersonal/JARVIS-AGI** | https://github.com/SreejanPersonal/JARVIS-AGI | Da saltare | Solo cloud, nessuna architettura locale utile |

**ONEPUNCHMAN411/Jarvis — da copiare:**
- **Strategy Memory**: SQLite che registra `(latency_ms, tokens_in, tokens_out, success)` per ogni skill. Il router impara il percorso più veloce per tipo di task.
- **ScreenWatcher self-throttle**: 3 dismiss → intervallo x2, 5 dismiss → pausa. Lista `quiet_apps` (Zoom, fullscreen). Requisito UX obbligatorio per il proactive agent.
- **Anti-pattern nel system prompt**: bandire "Certainly", "Of course", "I'd be happy to" e qualsiasi apertura formale. Ari via Federica TTS deve suonare naturale.
- **Safety timer per loop agentico**: `asyncio.wait_for` con timeout — evita che un tool bloccato congeli Swift.
- **Argument normalization**: pre-tool-call, normalizza output inconsistenti di Qwen3 (stringhe→int, ecc.).

**open-jarvis/OpenJarvis — da copiare:**
- **Complexity Router** (alta priorità): classifica query in <10ms (regex + lunghezza) → assegna token budget (1024 triviale, 16384 complessa). Per Qwen3 "thinking mode" moltiplica x2. Differenza di latenza 10x su M1 Max.
- **Skill overlay con few-shot auto-appresi**: dopo ogni esecuzione riuscita, salva `(input, output)` in `~/.ari/skills/<nome>/overlay.yaml`. Top-3 best injected come few-shot nel prompt successivo. Self-improvement senza fine-tuning.
- **Loop Guard** (critico per self-modification): hash chiamate identiche + rilevamento ping-pong A→B→A→B. Blocca al secondo ciclo. Evita deadlock nel self-modification engine.
- **Permission Store**: `always_approve`/`always_deny` in `~/.ari/permissions.yaml`. L'utente risponde "sempre sì" una volta → Ari gestisce autonomamente in futuro.
- **Morning Digest format**: mai numeri grezzi ("HRV 53" → "hai dormito bene"), max 250 parole, zero markdown, zero emoji, ottimizzato TTS. Cron alle 6:00.

### Assistenti vocali open-source

| Progetto | URL | Cosa studiare |
|---|---|---|
| Home Assistant Assist | https://www.home-assistant.io/voice_control/ | Pipeline vocale locale |
| wyoming-whisper | https://github.com/rhasspy/wyoming-whisper | STT per HA, architettura |
| Open Voice OS | https://openvoiceos.github.io | OS completo per voice assistant |

---

## Self-Modification e Agent Architecture

| Risorsa | URL | Note |
|---|---|---|
| Darwin Godel Machine | https://sakana.ai/dgm/ | Ricerca su AI self-modifying (sperimentale) |
| LangGraph | https://langchain-ai.github.io/langgraph/ | Graph-based agent orchestration |
| smolagents | https://github.com/huggingface/smolagents | HuggingFace agent framework leggero |
| Claude Code architecture | — | Pattern skill/tool da adottare per skill system |

---

## Home Assistant

| Risorsa | URL | Note |
|---|---|---|
| HA REST API | https://developers.home-assistant.io/docs/api/rest/ | API per controllo dispositivi |
| HA WebSocket API | https://developers.home-assistant.io/docs/api/websocket/ | Alternativa per eventi real-time |

---

## Idee da copiare (da athenaOld e da altri progetti)

### Da athenaOld

- **Skill format YAML frontmatter** — ogni skill ha metadata in YAML nell'header del file Python
- **Score decay per memoria** — i ricordi non si cancellano, il loro score decade nel tempo
- **Heading-aware chunking** — il path heading (`## Sezione > ### Sottosezione`) viene incluso nel chunk per dare contesto
- **CodeRepairService loop** — max 3 tentativi di fix prima di fermarsi e loggare
- **Backup pre-modifica automatico** — git commit prima di ogni modifica auto-generata
- **Profilo utente sempre in system prompt** — `roby.md` iniettato in ogni conversazione
- **Constitution separata dal system prompt** — `athena.md` definisce carattere, system prompt definisce tool e regole operative

### Da altri progetti

- **Jan.ai:** architettura plugin per aggiungere capabilities senza modificare core
- **Home Assistant Assist:** pipeline STT → intent recognition → action → TTS separata e modulare
- **smolagents:** tool chiamati come funzioni Python semplici, no overhead di framework
- **Open Voice OS:** gestione stato conversazione (idle / wake / listen / think / speak) come macchina a stati finiti

---

## Librerie Python — da valutare

```
# Core AI
ollama               # client Ollama Python
chromadb             # vector DB
faster-whisper       # STT (alternativa se subprocess whisper.cpp troppo lento)

# Server e async
fastapi
uvicorn[standard]
websockets

# Tools e system
gitpython            # self-modification versioning
watchdog             # hot reload skills
httpx                # HTTP async per HA e web search
pydantic             # validazione

# Audio (se STT in Python)
pyaudio              # cattura audio
numpy                # manipolazione waveform
```

---

## Note architetturali da ricordare

- **Non usare LangChain** — troppo overhead, astrazione che nasconde il flusso reale
- **Non usare AutoGen** — framework complesso per task semplici
- **Preferire funzioni Python semplici** per i tool — nessun framework agent
- **WebSocket puro** per Swift↔Python — no gRPC, no message queue per v1
- **SQLite per dati strutturati** — sessioni, log, preferenze; ChromaDB solo per vettori
