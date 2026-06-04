# Modulo: Memory System

**Stato:** parzialmente attivo  
**Aggiornato:** 04-06-2026

---

## Stato attuale — Short-term (attivo)

Implementato in `core/memory.py`.

- **Tipo**: deque Python, massimo **20 messaggi**
- **Persistenza**: nessuna — si azzera al riavvio del backend
- **System prompt**: caricato da `athena.md` ad ogni avvio
- **Formato**: lista `[{role: "user"|"assistant"|"system", content: "..."}]`

---

## Roadmap Memory (FASE 2)

### Long-term — SQLite

| Feature | Descrizione |
|---|---|
| Persistenza conversazioni | Ogni sessione salvata con timestamp su SQLite |
| Cronologia sidebar | Lista sessioni passate cliccabili |
| Session handoff | All'avvio, carica il contesto dell'ultima sessione |

**File previsti:**
- `core/database.py` — connessione SQLite, tabelle, query
- DB path: `~/Documents/athena/athena.db` (gitignored come `*.db`)

### Profilo Roby (FASE 2)

- Chi è Roby, cosa fa, preferenze
- Persistente, incluso automaticamente nel system prompt
- File: `brain/profilo.md` o tabella SQLite dedicata

---

## Roadmap Brain (FASE 5)

### Markdown Notes

- Note stile Obsidian in `brain/notes/`
- Link bidirezionali tra note
- Athena può leggere/creare note con conferma

### ChromaDB — Ricerca semantica

- Database vettoriale locale in `brain/chroma/`
- Embedding con `nomic-embed-text` via Ollama
- Athena cerca nelle note quando risponde (RAG locale)
- Knowledge graph visivo (in valutazione)

**Tutto il contenuto `brain/` è gitignored** — dati personali locali di Roby.

---

## Architettura futura

```
Memory System
├── short_term.py   ← deque (già esistente come memory.py)
├── database.py     ← SQLite long-term (FASE 2)
├── profilo.py      ← profilo Roby (FASE 2)
└── brain/
    ├── notes/      ← Markdown (FASE 5)
    └── chroma/     ← vettori ChromaDB (FASE 5)
```
