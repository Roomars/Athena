# Architettura Athena — Panoramica

**Versione:** 1.0  
**Aggiornato:** 04-06-2026

---

## Principio base

Athena è costruita a layer. Ogni layer parla solo con quello adiacente. Il frontend non sa nulla di Ollama. Il backend non sa nulla di Tauri. Aggiungere un modulo non tocca gli altri.

---

## I 5 Layer

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

## Layer ① — UI (PWA)

**File:** `static/index.html`, `static/manifest.json`, `static/sw.js`

- Interfaccia HTML/CSS/JS puro, nessun framework
- Comunicazione col backend via `fetch` (REST + streaming)
- Tauri la incapsula come app desktop nativa (menu bar)
- Design: bianco + azzurro `#0084FF`, font system, componenti essenziali

Stato: **attivo** (v0.2)

---

## Layer ② — Skill System

**Directory:** `modules/skills/` (da creare)

- Skill = file SKILL.md con istruzioni comportamentali per Athena
- Skill Loader carica le skill attive nel system prompt
- Skill Coach: skill predefinite (tactical-lab, psychology)
- Skill Creator: Athena aiuta Roby a creare nuove skill

Stato: **roadmap FASE 3**

---

## Layer ③ — Agent System

**Directory:** `modules/agents/` (da creare)

- Agent Engine: orchestratore di agenti task-oriented
- Agent File: legge/scrive file sul filesystem (con backup obbligatorio)
- Agent Shell: esegue comandi terminale (con doppia conferma)
- Agent Search: ricerca web/locale

Stato: **roadmap FASE 4**

---

## Layer ④ — Memory System

**File attuali:** `core/memory.py` (short-term, in-memory)

- **Short-term**: cronologia conversazione corrente (già implementata)
- **Long-term**: SQLite — conversazioni persistenti (FASE 2)
- **Brain**: ChromaDB + Markdown — knowledge base personale (FASE 5)
- **Profilo**: dati persistenti su Roby (chi è, cosa fa) (FASE 2)

Stato: **short-term attivo**, resto in roadmap

---

## Layer ⑤ — Kernel

**File:** `core/ollama.py`, `core/app.py`

- Ollama: endpoint locale `localhost:11434`, modello `qwen3:14b`
- Self Evolution: ciclo OSSERVA → PROPONE → BACKUP → CHIEDE → IMPLEMENTA (FASE 6)
- Observer: monitora pattern d'uso (FASE 6)

Stato: **Ollama attivo**, resto in roadmap

---

## Flusso di una richiesta chat

```
Roby digita → UI (JS) → POST /chat (FastAPI) → Memory.to_messages()
→ Ollama API (streaming) → StreamingResponse → UI aggiorna token per token
→ Memory.add(assistant, risposta completa)
```

---

## Regole architetturali

- Il frontend non importa mai logica Python direttamente
- La logica di business rimane in `core/` — mai in `static/` o `src-tauri/`
- Rust in `src-tauri/src/main.rs` è il minimo necessario per OS-level
- Ogni modulo futuro in `modules/` è autocontenuto
