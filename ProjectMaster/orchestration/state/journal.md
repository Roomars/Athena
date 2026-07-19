# Journal — Azioni Registrate

Questo file è **append-only**. Nessuna riga viene mai cancellata o modificata.
Ogni azione completata viene aggiunta in coda con timestamp, agente e risultato.

---

## Formato voce

```
## [DD-MM-AAAA HH:mm] — [Agente]
**Task:** [descrizione del task]
**Azione:** [cosa è stato fatto]
**File modificati:** [lista file, o "nessuno"]
**Esito:** [successo / parziale / fallito]
**Note:** [eventuali osservazioni rilevanti]
```

---

## Log

<!-- Le voci vengono aggiunte qui sotto in ordine cronologico -->
