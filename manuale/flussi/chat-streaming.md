# Flusso: Chat con Streaming

**Aggiornato:** 04-06-2026

---

## Percorso completo

```
Roby digita messaggio
        ↓
UI (JS) — fetch POST /chat { message, stream: true }
        ↓
FastAPI core/app.py — valida input, aggiunge a memory (role: user)
        ↓
memory.to_messages() → lista [{system}, ...storia..., {user: messaggio}]
        ↓
core/ollama.py — chat_stream(messages)
→ httpx POST localhost:11434/api/chat { model: qwen3:14b, stream: true }
        ↓
Ollama → stream di JSON lines
cada line: { message: { content: "token" }, done: false }
        ↓
FastAPI StreamingResponse — emit ogni chunk come testo plain
        ↓
UI — reader.read() loop → aggiorna DOM token per token
        ↓
Stream terminato → memory.add("assistant", risposta_completa)
```

---

## Flusso non-streaming (fallback)

```
UI — fetch POST /chat { message, stream: false }
        ↓
FastAPI → ollama.chat(messages) → attende risposta completa
        ↓
return { "reply": "testo completo" }
        ↓
UI — aggiorna DOM una volta sola
        ↓
memory.add("assistant", reply)
```

---

## Reset conversazione

```
UI — fetch DELETE /chat
        ↓
FastAPI — memory.clear()
        ↓
return { "status": "ok" }
```

---

## Gestione errori

| Scenario | Comportamento |
|---|---|
| Messaggio vuoto | FastAPI → HTTP 400 "Messaggio vuoto" |
| Ollama non raggiungibile | httpx ConnectError → HTTP 500 |
| Stream interrotto | Il chunk parziale rimane in UI, memory non aggiornata |
