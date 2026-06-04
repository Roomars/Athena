---
allowed-tools: Read, Edit, Bash
description: Salva lo stato corrente della sessione e pusha su GitHub — aggiorna stato_sessione.md, session_log e task_checkpoint.md. Funziona su Windows e macOS.
---

# Salva Sessione

Salva il progresso della sessione corrente e sincronizza con GitHub.

## Stato da aggiornare

- Data/ora: !`date "+%d-%m-%Y - %H:%M" 2>/dev/null || powershell -Command "Get-Date -Format 'dd-MM-yyyy - HH:mm'"`

---

## Passo 1 — Riepilogo sessione

Riassumi in modo sintetico dal contesto della conversazione:
- Cosa è stato fatto
- Decisioni prese (se presenti)
- Blockers risolti o aperti

---

## Passo 2 — Aggiorna `stato_sessione.md`

Leggi con Read: `manuale/regia_ai/stato_sessione.md`

Applica con Edit. Modifica SOLO le sezioni che cambiano:
- `Ultimo aggiornamento`: `DD-MM-AAAA - HH:mm`
- `Lavoro corrente`: riepilogo sessione corrente
- `Blocker attivi`: aggiorna (rimuovi se risolti, aggiungi se emersi)
- `Prossime priorità`: max 3, ordinate per urgenza
- `Changelog`: aggiungi riga in fondo — append-only, mai riscrivere

---

## Passo 3 — Aggiorna `task_checkpoint.md`

Leggi con Read: `manuale/regia_ai/task_checkpoint.md`

Se `status` è `IN_CORSO`, aggiorna con Edit:
- `updated`: data/ora corrente
- `branch`: !`git branch --show-current`
- `## Blocco corrente`: blocco appena completato
- `## Completati`: aggiungi `- [x] Blocco N — descrizione`
- `## Prossimo blocco`: prossimo blocco pianificato
- `## File toccati`: aggiungi file modificati (append)

Se `status` è `NESSUNO`: saltare questo passo.

---

## Passo 4 — Appendi voce in session_log

Leggi con Read: `manuale/regia_ai/session_log/YYYY-MM.md` (mese corrente).
Se il file non esiste: crearlo con intestazione `# Session Log — [Mese Anno]`.

Aggiungi in fondo con Edit:
- Data/ora, obiettivo sessione, lavoro svolto, decisioni prese, aperti rimasti.

---

## Passo 5 — Push su GitHub

Esegui con il tool Bash:

```bash
BRANCH=$(git branch --show-current)
STAMP=$(date '+%d%m%y.%H%M' 2>/dev/null || powershell -Command "Get-Date -Format 'ddMMyy.HHmm'")
git add -A && git commit -m "Save $STAMP" && git push origin $BRANCH
```

- Se non ci sono modifiche (`nothing to commit`): eseguire solo `git push origin $BRANCH`
- Se il push fallisce per divergenza: segnalare e suggerire `git pull --rebase` prima di riprovare
- Se il push va a buon fine: dichiarare "Push completato: Save [STAMP]"

---

## Passo 6 — Conferma

Dichiara: "Sessione salvata e pushata — `stato_sessione.md`, `task_checkpoint.md`, `session_log/YYYY-MM.md` aggiornati."
