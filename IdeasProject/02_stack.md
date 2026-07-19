# Athena — Stack Tecnologico

## Stack completo

| Componente | Tecnologia | Versione/Modello | Note |
|---|---|---|---|
| UI / Orb | SwiftUI + Metal | macOS 14+ | Shader Metal per animazioni orb |
| Menu bar | SwiftUI MenuBarExtra | macOS 13+ | Nativo, zero overhead |
| Wake word | Porcupine o custom | TBD | Sempre attivo, leggero |
| STT | whisper.cpp | large-v3-turbo | Metal nativo, italiano perfetto |
| TTS | Apple TTS nativa | it-IT Voce Premium | Zero latenza, zero dipendenze |
| Core daemon | Python + FastAPI | 3.12+ | Async, WebSocket, subprocess-safe |
| LLM veloce | MLX-lm → Qwen3 14B | 4bit (9GB) | Sempre in RAM, ottimizzato Apple Silicon |
| LLM potente | MLX-lm → Qwen2.5 32B | 4bit (21GB) | On-demand, swap con 14B |
| LLM vision | MLX-vlm → Qwen2-VL | 4bit (~8GB) | Analisi immagini, screen awareness |
| LLM fallback | NVIDIA NIM | Llama 3.3 70B | Solo se online + consenso utente |
| Vector DB | ChromaDB embedded | 0.5+ | Locale, in-process, zero server |
| Knowledge base | Orbit (MD) + AthenaInput | Markdown | Orbit converte, Ari indicizza |
| SQL | SQLite via aiosqlite | — | Sessioni, log, preferenze |
| Hot reload skills | watchdog + importlib | — | Skills si ricaricano senza restart |
| Versioning | Git locale | — | Ogni modifica trackable, rollback |
| Home automation | Home Assistant API | — | HTTP REST locale |
| Web search | DuckDuckGo (no key) | — | Privacy-first, zero costo |

---

## Gestione RAM — punto critico

M1 Max: 32GB unified memory totale.
OS + background: ~5-6GB
Athena Swift app: ~200MB
Python daemon + FastAPI: ~300MB
whisper.cpp large-v3: ~1.5GB
ChromaDB + SQLite: ~500MB

**Spazio disponibile per LLM: ~24GB**

| Scenario | RAM usata | Stato |
|---|---|---|
| Qwen3 14B in RAM | 9GB | ✅ Normale — sempre carico |
| Qwen3 14B + Qwen2.5 32B | 30GB | ⚠️ Troppo — swap su SSD |
| Solo Qwen2.5 32B | 21GB | ✅ OK per task pesanti |

**Regola:** Qwen3 14B è il modello primario, sempre carico.
Quando serve Qwen2.5 32B, Athena scarica il 14B, carica il 32B, poi ritorna al 14B.
Questo swap richiede ~15-30s — Athena lo comunica esplicitamente ("sto caricando il modello pesante...").

---

## Modelli e quando usarli

| Task | Modello | Perché |
|---|---|---|
| Conversazione, comandi rapidi | Qwen3 14B | Veloce, già in RAM |
| Codice complesso, architettura | Qwen2.5 32B | Qualità superiore |
| Self-modification proposal | Qwen2.5 32B | Task critico, qualità massima |
| Trascrizione voce | whisper.cpp | Separato dall'LLM |
| Embedding documenti | nomic-embed-text via Ollama | Leggero, locale |
| Fallback task pesanti | NVIDIA NIM | Solo online, solo con consenso |

---

## Python — dipendenze core

```
fastapi
uvicorn[standard]
websockets
mlx-lm          # LLM inference Apple Silicon (sostituisce ollama)
mlx-vlm         # Vision LLM (screen awareness, analisi immagini)
huggingface_hub # download modelli da HuggingFace
chromadb        # vector DB embedded
aiosqlite       # SQLite async
watchdog        # file watcher per hot reload skills
gitpython       # git operations per self-modification
httpx           # HTTP client async (Home Assistant, web)
pydantic        # validazione modelli dati
```

**Nota:** Ollama rimosso. MLX-lm è più veloce su Apple Silicon e non richiede server separato — l'inference gira in-process nel daemon Python.

---

## Swift — dipendenze

```
SwiftUI (built-in)
Metal (built-in)
AVFoundation (audio I/O)
whisper.cpp (via Swift Package o xcframework)
```

Nessuna dipendenza Swift esterna non necessaria.
Tutto ciò che richiede librerie esterne pesanti → spostare in Python.

---

## Decisioni di stack da NON rifare

Cosa ha già risolto athenaOld e non va messo in discussione:
- ✅ Swift per UI macOS (giusto)
- ✅ Ollama come LLM server locale (giusto)
- ✅ NVIDIA NIM come fallback gratuito (giusto)
- ✅ Whisper per STT italiano (giusto)
- ✅ Apple TTS per output voce (giusto)
- ✅ Obsidian vault come knowledge base (giusto)
- ✅ Git per versioning (giusto)

Cosa cambia rispetto ad athenaOld:
- ❌ → ✅ Python per il brain (invece di Swift puro)
- ❌ → ✅ MLX-lm invece di Ollama (più veloce su Apple Silicon, vision inclusa)
- ❌ → ✅ ChromaDB per vector search (invece di GRDB embeddings)
- ❌ → ✅ Self-modification come feature di prima classe (non FASE 10 mai implementata)
- ❌ → ✅ Due modalità UI: Voice (notch) + Chat (pannello)
- ❌ → ✅ AI chiamata Ari (progetto Athena)
