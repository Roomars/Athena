# Modulo: Core Backend

**Cartella:** `core/`  
**Stato:** attivo (v0.2)  
**Aggiornato:** 04-06-2026

---

## File

### `core/app.py` — FastAPI entry point

Endpoint esposti:
| Metodo | Path | Funzione |
|---|---|---|
| GET | `/` | Serve `static/index.html` |
| POST | `/chat` | Riceve messaggio, aggiunge a memory, chiama Ollama |
| DELETE | `/chat` | Svuota la memoria della conversazione |

Funzionamento streaming:
- `req.stream = true` → `StreamingResponse` con `media_type="text/plain"`
- Ogni chunk viene inviato al frontend token per token via `generate()`
- La risposta completa viene aggiunta alla memory solo alla fine dello stream

CORS configurato per: `http://localhost:8000` e `http://127.0.0.1:8000`

---

### `core/ollama.py` — Client Ollama

- Punta a `http://localhost:11434`
- Modello: `qwen3:14b`
- Client: `httpx.AsyncClient` con timeout 120 secondi
- `chat()`: risposta sincrona (non streaming)
- `chat_stream()`: generatore asincrono, emette chunk stringa per stringa

---

### `core/memory.py` — Memoria conversazione

- Implementa una **deque** con massimo **20 messaggi** (short-term)
- Il system prompt viene caricato da `athena.md` (la Costituzione)
- Metodi: `add(role, content)`, `to_messages()`, `clear()`
- `to_messages()` restituisce la lista messaggi nel formato Ollama/OpenAI `[{role, content}]`
- Il system prompt è sempre il primo elemento

---

## Avvio

```bash
./start.sh
# oppure direttamente:
uvicorn core.app:app --reload --port 8000
```

Backend disponibile su `http://localhost:8000`

---

## Limitazioni attuali

- Memory è **in-RAM**: riavviare il backend azzera la conversazione
- Nessuna persistenza → da risolvere in FASE 2 con SQLite
- Il system prompt viene riletto da `athena.md` ad ogni avvio (non in runtime)
