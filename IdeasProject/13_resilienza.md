# Athena — Resilienza e Gestione Errori

## Principio

Athena non deve mai bloccarsi silenziosamente.
Se qualcosa va storto: degrada gracefully, comunica cosa e' successo, riprova dove possibile.
Un errore lento e comunicato e' meglio di un crash muto.

---

## Gerarchia di risposta agli errori

```
1. Riprova automaticamente (max 3 volte, backoff esponenziale)
2. Degrada a modalita' ridotta (funziona con meno capacita')
3. Notifica Roby con messaggio chiaro e azione suggerita
4. Log dettagliato per diagnosi
```

---

## Scenari di failure e comportamento

### Ollama non risponde

**Cause:** Ollama crashato, porta 11434 occupata, modello non caricato.

**Comportamento:**
```
Athena tenta 3 richieste con backoff 1s/2s/4s
  ↓ tutte fallite
Se NVIDIA fallback abilitato → tenta NVIDIA (con avviso "uso cloud")
Se NVIDIA non abilitato → risposta testo: "Il motore AI non risponde.
  Verifica che Ollama sia attivo (ollama serve). Riprovo tra 30s."
Tenta riavvio automatico Ollama via subprocess ogni 30s (max 3 volte)
Se Ollama non si riavvia → notifica macOS con istruzioni
```

**Modalita' degradata:** Athena risponde con capabilities limitate
(no LLM = no conversazione, solo skills che non richiedono LLM: time, calendar, reminders).

---

### Python daemon crashato

**Rilevato da:** Swift verifica /health ogni 5s.

**Comportamento Swift:**
```
/health non risponde per 10s
  → Swift rilancia il daemon Python (subprocess restart)
  → Attende 5s
  → Se torna online: orb mostra brevemente "riconnesso"
  → Se non torna: dopo 3 tentativi → notifica errore + log
```

**Recovery:** il daemon Python al riavvio carica l'ultimo stato da SQLite
(working memory si azzera, ma settings e memoria a lungo termine sono intatte).

---

### Whisper fallisce la trascrizione

**Cause:** audio troppo corto, rumore eccessivo, file corrotto.

**Comportamento:**
```
Trascrizione vuota o errore
  → Athena dice: "Non ho capito, puoi ripetere?"
  → Riattiva ascolto automaticamente
  → Se fallisce 3 volte consecutive: "Problema con il microfono.
    Prova input testo." + passa a modalita' testo-only temporanea
```

---

### Google Drive offline / AthenaInput non accessibile

**Causa:** internet assente, Drive non montato, path cambiato.

**Comportamento:**
```
watchdog non trova la cartella AthenaInput
  → Athena continua a funzionare normalmente (usa la knowledge locale)
  → Log: "AthenaInput non raggiungibile — uso solo knowledge locale"
  → Non notifica Roby a meno che non provi a indicizzare qualcosa
  → Quando Drive torna online: watchdog riprende automaticamente
```

---

### ChromaDB corrotto o inaccessibile

**Causa:** crash durante scrittura, disco pieno, permessi.

**Comportamento:**
```
Errore ChromaDB
  → Athena prova a riaprire il DB
  → Se riapertura fallisce: backup del DB corrotto con timestamp
  → Crea nuovo DB vuoto
  → Avvia re-index completo da /vault/athena/knowledge/ in background
  → Notifica: "Indice memoria ripristinato. Re-indicizzazione in corso..."
  → Funziona normalmente durante re-index (senza retrieval fino al completamento)
```

---

### Self-modification — xcodebuild fallisce

**Causa:** errore Swift, dipendenza mancante, conflitto.

**Comportamento:**
```
xcodebuild exit code != 0
  → Git rollback automatico (git checkout HEAD -- [file modificati])
  → Log errore completo salvato in /diagnostics/[timestamp]-swift-build.log
  → Notifica a Roby: "Build Swift fallita. Modifica annullata. [log sintetico]"
  → Proposta alternativa: "Vuoi che riprovi con un approccio diverso?"
  → Max 3 tentativi totali, poi stop e log
```

---

### Disco quasi pieno

**Soglie:**
- < 5GB liberi: avviso "Spazio disco basso — alcune funzioni potrebbero rallentare"
- < 1GB liberi: sospendi indicizzazione nuovi documenti + avviso urgente
- < 500MB liberi: blocca self-modification (no nuovi file) + avviso critico

---

### NVIDIA fallback — errore API

**Causa:** rate limit, API key scaduta, internet assente.

**Comportamento:**
```
NVIDIA risponde con errore
  → Fallback a Qwen3 14B locale (con nota: "uso modello locale")
  → Se anche 14B non disponibile: comunica errore
  → Non ritentare NVIDIA per 5 minuti (evita rate limit cascade)
```

---

## Logging

**File:** `~/Library/Logs/Athena/athena.log`
Rotazione automatica: max 10MB, max 5 file (50MB totale).

**Formato:**
```
2026-06-14 10:23:45 [INFO] [router] input ricevuto: "cerca notizie su..."
2026-06-14 10:23:45 [INFO] [skill:web_search] esecuzione query DuckDuckGo
2026-06-14 10:23:46 [INFO] [skill:web_search] 5 risultati trovati, elaborazione completata
2026-06-14 10:23:46 [INFO] [llm] streaming risposta, 247 token generati
2026-06-14 10:23:47 [ERROR] [ollama] timeout dopo 30s — tentativo 1/3
```

**Livelli:**
- `DEBUG`: solo in development mode (disabilitato in produzione)
- `INFO`: flusso normale (ogni request/response, ogni skill eseguita)
- `WARN`: degradazione (fallback usato, retry in corso)
- `ERROR`: failure (crash, timeout, rollback)

**Diagnostics panel:** accessibile da menu bar → "Diagnostica"
Mostra: ultima ora di log, stato componenti, modelli caricati, ChromaDB stats.

---

## Crash-Safe Gates (pattern da LUCE)

Due gate indipendenti garantiscono cleanup anche se l'app crasha:

**Gate 1 — atexit handler (Python):**
```python
import atexit

def cleanup_on_exit():
    """Eseguito sempre all'uscita, anche in caso di crash."""
    mlx_model.unload()           # Libera RAM modello
    chromadb_client.close()      # Chiude connessione DB
    websocket_server.close()     # Chiude WebSocket
    save_session_state()         # Salva stato sessione

atexit.register(cleanup_on_exit)
```

**Gate 2 — deinit Swift:**
```swift
class AthenaCore {
    deinit {
        // Eseguito anche se Swift crasha
        pythonDaemon.terminate()
        audioEngine.stop()
        porcupineManager.delete()
    }
}
```

Questi due gate insieme garantiscono che:
- Il modello MLX venga sempre scaricato dalla RAM
- Il daemon Python venga sempre terminato
- La sessione venga sempre salvata
- Il microfono venga sempre rilasciato

---

## Health Check integrato

Athena esegue un self-check ogni 60s in background:

```python
checks = {
    "ollama": ping porta 11434,
    "chromadb": query di test,
    "vault_input": path accessibile,
    "disk_space": GB liberi,
    "whisper": modello caricato,
}
# Se tutti OK: nessuna azione
# Se qualcosa KO: log + eventuale notifica
```

Risultato visibile nel diagnostics panel e accessibile via "Athena, come stai?".
