---
allowed-tools: Read, Edit, Bash
description: Chiusura sessione — aggiorna sessione.md e push su GitHub
---

# Chiudi Sessione

## Stato corrente

- Data/ora chiusura: !`date "+%d-%m-%Y - %H:%M"`

Leggi con il tool Read: `sessione.md`

## Checklist chiusura

### 1. Riepilogo

Se non già noto dal contesto, chiedi:
"Dimmi cosa abbiamo fatto in questa sessione."

### 2. Aggiorna `sessione.md`

Con Edit aggiorna SOLO le sezioni che cambiano:
- `Ultimo aggiornamento`: data/ora corrente `DD-MM-AAAA - HH:mm`
- `Lavoro corrente`: descrizione sintetica della sessione
- `Prossime priorità`: max 3, ordinate per urgenza
- `Blocker attivi`: aggiorna (rimuovi se risolti)
- `Changelog`: aggiungi riga in fondo — mai riscrivere righe esistenti

### 3. Conferma

Dichiara: "Sessione chiusa. File aggiornati: sessione.md"

### 4. Push automatico

```bash
STAMP=$(date '+%d%m%y.%H%M') && git add -A && git commit -m "Update $STAMP" && git push origin $(git branch --show-current)
```

Se non ci sono modifiche (`nothing to commit`): eseguire solo `git push`.
Se il push fallisce: segnalarlo con il messaggio di errore.
Dichiarare: "Push completato: Update [STAMP]"
