# Athena — Contesto AI

Questo file viene caricato automaticamente ad ogni sessione e definisce le regole operative critiche per lo sviluppo di **Athena**.

---

## Descrizione Progetto

Athena è una segretaria AI personale di Roby. Gira completamente in locale su Apple M1 Max, senza cloud, senza abbonamenti. Il modello AI è **Qwen3 14B** servito da Ollama sulla porta 11434.

Stack:
- **Backend**: Python + FastAPI (streaming SSE)
- **Frontend**: HTML + CSS + JS puro (PWA)
- **Desktop**: Tauri 2 (menu bar, system tray)
- **AI**: Qwen3 14B via Ollama (localhost:11434)
- **Database**: SQLite (da implementare)
- **Brain**: Markdown + ChromaDB (da implementare)

---

## Regole Operative Bloccate

- **Lingua**: Italiano sempre, sia nelle risposte che nella documentazione
- **Timezone**: `Europe/Rome` — formato data/ora: `DD-MM-AAAA - HH:mm`
- **Fonte di verità**: `manuale/` > codice reale > chat
- **Co-working**: Un blocco alla volta. Stop, conferma utente, poi il blocco successivo
- **Backup**: Prima di ogni modifica automatica creare backup in `backups/YYYY-MM-DD_HH-MM/`
- **Roby non sa programmare**: spiegare sempre cosa fare, non solo il codice

---

## Architettura — 5 Layer

```
┌─────────────────────────────────────────────┐
│  ① UI — Interfaccia PWA                     │
│  Quick Entry · Markdown · Cronologia        │
├─────────────────────────────────────────────┤
│  ② Skill System                             │
│  Skill Loader · Coach · Creator             │
├─────────────────────────────────────────────┤
│  ③ Agent System                             │
│  Agent Engine · File · Shell · Search       │
├─────────────────────────────────────────────┤
│  ④ Memory System                            │
│  Short-term · Long-term · Brain · Profilo   │
├─────────────────────────────────────────────┤
│  ⑤ Kernel                                  │
│  Ollama · Self Evolution · Observer         │
└─────────────────────────────────────────────┘
```

---

## Struttura Progetto

```
athena/
├── core/           ← backend Python (FastAPI, Ollama, Memory)
├── static/         ← frontend HTML/CSS/JS (PWA)
├── src-tauri/      ← app desktop Tauri 2
├── modules/        ← moduli futuri (skill, agent, brain)
├── brain/          ← dati brain locali (gitignored)
├── backups/        ← backup pre-modifica (gitignored)
├── manuale/        ← documentazione di progetto (fonte di verità)
└── self/           ← changelog Athena
```

---

## Linee Guida per il Codice

**Python:**
- Type hints sempre — evitare `Any` non motivato
- Nessuna operazione bloccante nel thread principale — usare `async/await`
- Eccezioni gestite nei layer profondi, propagate come messaggi leggibili all'UI
- Nessun file > 300 righe — spezzare prima di continuare

**JavaScript:**
- Nessun framework — HTML/CSS/JS puro
- Nessun valore di stile hardcodato nel JS — variabili CSS
- Streaming display: `fetch` con `ReadableStream` o `EventSource`
- Stato UI sempre esplicito: vuoto / caricamento / dati / errore

**Tauri:**
- La logica di business rimane in Python — Rust solo per OS-level
- Ogni `invoke()` ha gestione errore lato JS

---

## Ufficio AI — Struttura

### Comandi di sessione
| Comando | Quando |
|---|---|
| `/Apri Sessione` | Inizio sessione — sync GitHub, health check, stato progetto |
| `/Salva Sessione` | Durante la sessione — salva stato e pusha su GitHub |
| `/Chiudi Sessione` | Fine sessione — checklist completa e push finale |

### Team di agenti (`.claude/agents/`)

**Core Team:**
| Agente | Modello | Quando |
|---|---|---|
| `core/architetto` | Opus | Decisioni strutturali — chiamare PRIMA di scrivere codice |
| `core/senior-dev` | Sonnet | Implementazione Python/FastAPI/JS |
| `core/qa-engineer` | Sonnet | Test e validazione — chiamare DOPO senior-dev |
| `core/tech-writer` | Haiku | Documentazione in `manuale/` |
| `core/build-engineer` | Haiku | Packaging Tauri, dipendenze, release |

**Specialist Athena:**
| Agente | Modello | Quando |
|---|---|---|
| `specialist/tauri-specialist` | Sonnet | Tauri 2, bridge JS/Rust, menu bar, bundle |
| `specialist/ui-web-specialist` | Sonnet | HTML/CSS/JS PWA, streaming, design system |

### Fonte di verità del progetto (`manuale/`)
| Cartella | Contenuto |
|---|---|
| `manuale/regia_ai/` | Stato sessione, checkpoint task, errori appresi, session log |
| `manuale/architettura/` | Panoramica, stack, decisioni DEC-* |
| `manuale/moduli/` | Documentazione di ogni modulo/layer |
| `manuale/flussi/` | Un file per ogni flusso di esecuzione |
| `manuale/gui/` | Design system, componenti, UX |
| `manuale/roadmap/` | Backlog e decisioni architetturali |

---

## Setup di Sviluppo

```bash
# Crea venv
python -m venv .venv
source .venv/bin/activate   # macOS
# .venv\Scripts\activate    # Windows

# Installa dipendenze
pip install -r requirements.txt

# Avvia backend
./start.sh
# oppure: uvicorn core.app:app --reload --port 8000

# Build desktop (macOS)
./build-mac.sh
```

---

## Workflow Multi-macchina (Mac + Windows)

1. **Inizio sessione** → `/Apri Sessione` — sync GitHub, health check
2. **Durante la sessione** → `/Salva Sessione` — salva e pusha
3. **Fine sessione** → `/Chiudi Sessione` — push finale

La prossima macchina trova tutto aggiornato.
