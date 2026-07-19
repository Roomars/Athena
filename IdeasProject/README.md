# Athena 2.0 — IdeasProject

Documenti di progettazione. Da leggere e validare prima di scrivere codice.

## Indice

| File | Contenuto |
|---|---|
| [00_visione.md](00_visione.md) | Identità, carattere, vincoli non negoziabili |
| [01_architettura.md](01_architettura.md) | Split Swift/Python, comunicazione, ciclo di vita |
| [02_stack.md](02_stack.md) | Tecnologie scelte con motivazione, gestione RAM |
| [03_cervello.md](03_cervello.md) | 4 livelli memoria, RAG, Obsidian vault |
| [04_skills.md](04_skills.md) | Sistema skills, hot reload, routing |
| [05_self_improvement.md](05_self_improvement.md) | Self-modification engine, ciclo completo, sicurezza |
| [06_voce.md](06_voce.md) | Pipeline STT/TTS, wake word, modalità silenziosa |
| [07_ui_orb.md](07_ui_orb.md) | Orb animato, Metal shader, struttura UI Swift |
| [08_eredita.md](08_eredita.md) | Cosa copiare da athenaOld, cosa scartare |
| [09_coerenza.md](09_coerenza.md) | Verifica coerenza tra moduli, punti aperti |
| [10_roadmap.md](10_roadmap.md) | 10 fasi con dipendenze, mappa visiva, concern trasversali |
| [11_riferimenti.md](11_riferimenti.md) | Link esterni, progetti da studiare, idee da copiare |
| [12_operativita.md](12_operativita.md) | First run, settings.json, auto-start, privacy mode, context window |
| [13_resilienza.md](13_resilienza.md) | Failure modes, recovery, logging, health check |
| [14_modalita.md](14_modalita.md) | Voice (notch) + Chat (pannello), come si interagisce, prompt, file |
| [15_jarvis_features.md](15_jarvis_features.md) | Feature Jarvis: proattività, screen awareness, sub-agenti, progetti, personalità |
| [16_orbit_knowledge.md](16_orbit_knowledge.md) | Orbit pipeline, Books→MD, Local NotebookLM, knowledge_ops skill |
| [17_desktop_mode.md](17_desktop_mode.md) | Modalità Desktop: layout, input field, artifacts, progetti, widget system, MCP |

## Decisioni prese

| # | Decisione | Scelta |
|---|---|---|
| D01 | Architettura | Swift UI + Python Brain (split via WebSocket) |
| D02 | LLM primario | Qwen3 14B (sempre in RAM) |
| D03 | LLM potente | Qwen2.5 32B (on-demand, swap con 14B) |
| D04 | LLM fallback | NVIDIA NIM (opt-in, con avviso) |
| D05 | STT v1 | Python subprocess (semplice, +200ms accettabile) |
| D06 | STT v2 | Swift xcframework whisper.cpp (FASE 9) |
| D07 | TTS | Apple TTS nativa, voce italiana premium |
| D08 | Wake word | Porcupine SDK, "Athena" custom |
| D09 | Vector DB | ChromaDB embedded |
| D10 | Vault Roby | Google Drive (read-only per Athena) |
| D11 | Vault Athena | Locale `/vault/athena/` (privacy totale) |
| D12 | Hot reload | watchdog + importlib per skills Python |
| D13 | Versioning | Git locale per self-modification rollback |
| D14 | TTS voice | Federica (Premium) it_IT — unica voce Premium installata |
| D15 | Ispirazione skill format | OpenClaw SOUL.md/SKILL.md → adattato in YAML frontmatter Python |
| D16 | Ispirazione backend | Odysseus FastAPI structure + ChromaDB integration |
| D17 | Vault input | Google Drive/AthenaInput/ — Roby ci mette file, Athena monitora e copia in locale |
| D18 | Vault Athena | /vault/athena/ locale — knowledge/ (copie elaborate) + notes/ (scrittura Athena) |
| D19 | Feed documenti | Ibrido: Roby sceglie cosa mettere in AthenaInput/, Athena elabora automaticamente |
| D20 | Scope dispositivi | Solo Mac per ora (iPhone accede a AthenaInput/ via Google Drive app) |
| D21 | Nome AI | **Ari** (progetto = Athena, AI = Ari) |
| D22 | Voice mode | Ari vive nel notch del MacBook (209x32px), si espande su hover/wake |
| D23 | Chat mode | Pannello flottante stile Claude Desktop, testo + allegati + markdown |
| D24 | Inference engine | MLX-lm (sostituisce Ollama, più veloce su Apple Silicon) |
| D25 | Vision | MLX-vlm per analisi immagini e screen awareness |
| D26 | Notch reference | Boring Notch (open-source) per WindowManager + MouseTracker pattern |
| D27 | Books→MD | Orbit (software separato) → AthenaInput/ → Ari indicizza |
| D28 | Local NotebookLM | Feature nativa Ari: notebook, Q&A con citazioni, sommari, FAQ, briefing audio |
| D29 | Hotkey globale | CGEvent tap OS-level (pattern LUCE) — funziona anche su lock screen |
| D30 | Crash safety | atexit (Python) + deinit (Swift) per cleanup garantito anche su crash |
| D31 | TTS roadmap | Apple Federica Premium (FASE 1-6) → valutare Kokoro TTS (FASE 10) |
| D32 | P2P sync | UDP broadcast + TCP (pattern Balance-Separator) per Mac↔Windows senza server |
| D33 | RAG filtering | Binary filtering (pattern stack) — scarta .pyc/.o/node_modules dal codebase RAG |
| D34 | GitHub repo | https://github.com/Roomars/Athena — repo ufficiale |
| D35 | Artifacts inline | Sì, come Claude Desktop — rendered nel pannello chat |
| D36 | Widget system | Artifact → ↗ apre finestra floating draggable sul desktop |
| D37 | Tasto destro widget | Context menu: chiudi, pinna, esporta, invia in chat |
| D38 | Skill acquisition | Ari acquisisce skill da Claude Desktop MCP: genera wrapper Python nativi, li salva in /skills/imported/ — diventano capacità proprie permanenti |
| D39 | Progetti | Contesti isolati con knowledge, system prompt e storia dedicata |
| D40 | DiffWidget | Self-modification proposal: sempre widget floating, mai inline |
| D41 | Widget persistenza | Posizioni salvate in widget_state.json, pinnati ripristinati al riavvio |

## Punti ancora aperti

- [ ] Voce Apple TTS: quale voce italiana premium scegliere? (verificare voci installate)
- [ ] Vault Roby: path Google Drive da configurare nelle settings
- [ ] Piper: valutare come alternativa TTS in FASE 10

## Stato sviluppo

- [x] Visione definita
- [x] Architettura definita
- [x] Stack scelto
- [x] Decisioni principali prese
- [x] Roadmap scritta
- [x] Operativita' (first run, config, auto-start, privacy mode)
- [x] Resilienza (failure modes, logging, health check)
- [x] Roadmap migliorata (dipendenze, mappa visiva, concern trasversali)
- [ ] Struttura cartelle progetto creata
- [ ] Sviluppo FASE 1 iniziato
