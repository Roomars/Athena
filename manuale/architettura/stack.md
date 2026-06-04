# Stack Tecnico — Athena

**Aggiornato:** 04-06-2026

---

## Componenti attivi

| Componente | Tecnologia | Versione | Note |
|---|---|---|---|
| Modello AI | Qwen3 14B | — | via Ollama, porta 11434 |
| Backend | Python + FastAPI | — | streaming SSE, async |
| Frontend | HTML + CSS + JS | — | PWA, nessun framework |
| Desktop | Tauri 2 | 2.x | menu bar, system tray |
| HTTP client (Python) | httpx | — | client async per Ollama |
| Build | Cargo / Rust | — | solo per Tauri |

---

## Componenti in roadmap

| Componente | Tecnologia | Fase |
|---|---|---|
| Database | SQLite | FASE 2 |
| ORM | SQLModel o raw sqlite3 | FASE 2 |
| Brain | ChromaDB + Markdown | FASE 5 |
| Embedding | nomic-embed-text (Ollama) | FASE 5 |
| Agenti | custom Agent Engine | FASE 4 |

---

## Dipendenze Python (`requirements.txt`)

Vedere il file `requirements.txt` per la lista completa e aggiornata.
Dipendenze chiave:
- `fastapi` — web framework
- `uvicorn` — ASGI server
- `httpx` — client HTTP async
- `pydantic` — validazione dati

---

## Porte locali

| Servizio | Porta |
|---|---|
| FastAPI backend | 8000 |
| Ollama | 11434 |

---

## Piattaforme target

- **macOS** (Apple M1 Max) — macchina principale di sviluppo
- **Windows** — macchina secondaria

La codebase è cross-platform. Percorsi file usano `pathlib.Path`. Build Tauri gestisce icone e bundle per entrambe le piattaforme.

---

## Avvio sviluppo

```bash
# Backend
source .venv/bin/activate
./start.sh
# → http://localhost:8000

# Build app desktop
./build-mac.sh

# Test
python -m pytest
```
