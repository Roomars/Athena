# Athena — Architettura

## Principio fondamentale

Due layer ben separati, un canale di comunicazione.
Nessun layer invade il dominio dell'altro.

```
┌──────────────────────────────────────────────┐
│              SWIFT LAYER                      │
│         (tutto ciò che tocca macOS)           │
│                                               │
│  Menu Bar App  ←→  Orb (Metal shader)        │
│  Voice Manager (STT in + TTS out)            │
│  Wake word detector                          │
│  System integration (notifiche, shortcuts)   │
│                                               │
│         WebSocket ws://localhost:8765         │
└──────────────────┬───────────────────────────┘
                   │ JSON messages
┌──────────────────▼───────────────────────────┐
│              PYTHON LAYER                     │
│         (tutto ciò che tocca l'AI)            │
│                                               │
│  Core daemon (FastAPI + asyncio)             │
│  Router → Planner → Executor                 │
│  LLM Engine (Ollama)                         │
│  Memory Engine (ChromaDB + SQLite)           │
│  Skills Registry                             │
│  Self-Modification Engine                    │
│                                               │
└──────────────────────────────────────────────┘
```

---

## Perché questo split (vs. Swift puro come in athenaOld)

La vecchia Athena era Swift puro. Problemi:
- Ecosistema AI quasi assente in Swift
- Self-improvement impossibile da implementare (nessun hot reload, compilazione lenta)
- Integrazione con Whisper, ChromaDB, Ollama — tutto bridging complicato
- FASE 10 (self-improve) è rimasta a 0% esattamente per questo

Con Python per il cervello:
- Hot reload istantaneo delle skills (watchdog + importlib)
- Accesso nativo a Ollama, ChromaDB, whisper.cpp, tutto
- Self-modification praticabile: Python si ricarica, Swift si ricompila solo se necessario
- Ecosistema AI completo senza bridging

Swift rimane però perché:
- Menu bar e orb richiedono API macOS native
- Metal per gli shader dell'orb
- Voice I/O (microfono + speaker) meglio gestito lato nativo
- Wake word sempre attivo = processo leggero, Swift è il candidato giusto

---

## Comunicazione Swift ↔ Python

**Protocollo:** WebSocket locale (porta 8765)
**Formato:** JSON

Messaggi Swift → Python:
```json
{ "type": "user_input", "content": "testo o trascrizione", "mode": "voice|text" }
{ "type": "ping" }
```

Messaggi Python → Swift:
```json
{ "type": "response_chunk", "content": "token", "stream": true }
{ "type": "response_done", "state": "idle" }
{ "type": "orb_state", "state": "thinking|listening|speaking|idle" }
{ "type": "confirm_request", "proposal": "...", "diff": "..." }
```

---

## Ciclo di vita

1. **Boot:** Swift app parte → lancia Python daemon come subprocess → WebSocket handshake
2. **Idle:** Orb in pulsazione lenta. Wake word / hotkey in ascolto continuo (Swift).
3. **Input voce:** Whisper trascrive → Swift invia testo a Python via WS
4. **Input testo:** Utente scrive nell'orb UI → Swift invia a Python via WS
5. **Elaborazione:** Python ragiona, chiama tools, streaming token → Swift riceve e anima orb
6. **Output:** Python invia risposta → Swift legge con TTS (o mostra testo in silenzioso)
7. **Modifica codice:** Python propone diff → Swift mostra confirm dialog → utente approva → Python applica

---

## Avvio e shutdown

```bash
# Python daemon (avviato da Swift come subprocess)
python3 -m athena.core --port 8765

# Swift verifica che il daemon sia attivo via /health endpoint
# Se non risponde in 3s → rilancia
# Shutdown: Swift termina subprocess Python prima di chiudersi
```

---

## Regola critica — separazione responsabilità

| Cosa | Layer |
|---|---|
| Rendering UI, animazioni orb | Swift |
| Permessi microfono, speaker | Swift |
| Wake word detection | Swift |
| Trascrizione audio (whisper.cpp) | Swift (via lib C) o Python (via subprocess) |
| TTS output | Swift (Apple TTS nativa) |
| Ragionamento LLM | Python |
| Memoria, RAG, embeddings | Python |
| Skills, tools, azioni | Python |
| Self-modification engine | Python |
| Git versioning | Python |
| Comunicazione con Home Assistant | Python |
| Ricerca web | Python |
