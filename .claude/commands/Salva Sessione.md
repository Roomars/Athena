---
allowed-tools: Read, Edit, Bash
description: Salva lo stato corrente della sessione senza chiudere — aggiorna sessione.md
---

# Salva Sessione

## Stato da aggiornare

- Data/ora: !`date "+%d-%m-%Y - %H:%M"`

## Passi

### 1. Riepilogo

Riassumi dal contesto della conversazione:
- Cosa è stato fatto
- Decisioni prese (se presenti)
- Blockers risolti o aperti

### 2. Aggiorna `sessione.md`

Leggi il contenuto corrente con il tool Read: `sessione.md`

Poi applica le modifiche con Edit. Modifica SOLO le sezioni che cambiano:
- `Ultimo aggiornamento`: `DD-MM-AAAA - HH:mm`
- `Lavoro corrente`: aggiorna con il riepilogo
- `Blocker attivi`: aggiorna
- `Prossime priorità`: max 3, ordinate per urgenza
- `Changelog`: aggiungi riga in fondo (append-only, non cancellare righe esistenti)

### 3. Conferma

Dichiara: "Sessione salvata — `sessione.md` aggiornato."
