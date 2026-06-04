---
allowed-tools: Read, Edit, Bash
description: Chiusura sessione Orbit Desktop — aggiorna stato_sessione.md, session_log e task_checkpoint.md con checklist guidata, poi pusha su GitHub. Funziona su Windows e macOS.
---

# Chiudi Sessione

Esegui chiusura sessione Orbit Desktop guidata.

## Stato corrente

- Data/ora chiusura: !`date "+%d-%m-%Y - %H:%M" 2>/dev/null || powershell -Command "Get-Date -Format 'dd-MM-yyyy - HH:mm'"`

Leggi con il tool Read: `manuale/regia_ai/stato_sessione.md`

---

## Checklist chiusura — esegui in ordine

### 1. Raccogli il riepilogo

Se non già noto dal contesto, chiedi all'utente:
"Dimmi cosa abbiamo fatto in questa sessione" (lavoro completato, decisioni prese, problemi aperti).

### 2. Aggiorna `stato_sessione.md`

Aggiorna con Edit SOLO le sezioni che cambiano (append-only sul changelog):
- `Ultimo aggiornamento`: `DD-MM-AAAA - HH:mm`
- `Lavoro corrente`: descrizione sintetica della sessione appena conclusa
- `Blocker attivi`: aggiorna (rimuovi se risolti, aggiungi se emersi)
- `Prossime priorità`: max 3, ordinate per urgenza
- `Changelog`: aggiungi riga in fondo — mai riscrivere

### 3. Chiudi `task_checkpoint.md`

Leggi con Read: `manuale/regia_ai/task_checkpoint.md`

- Task **completato** → `status: COMPLETATO`, aggiorna `updated`
- Task **ancora aperto** → lascia `IN_CORSO`, aggiorna `updated` e `## Prossimo blocco`
- `status: NESSUNO` → saltare questo passo

### 4. Scrivi log sessione

Leggi con Read: `manuale/regia_ai/session_log/YYYY-MM.md` (mese corrente).
Se non esiste: crearlo con intestazione `# Session Log — [Mese Anno]`.

Aggiungi voce append-only con Edit:
data/ora — obiettivo — lavoro svolto — decisioni — aperti.

### 5. Verifica decisioni e backlog

- **Decisioni architetturali approvate**? → Registrare in `manuale/roadmap/decisioni.md` come DEC-[N+1]
- **Punti aperti nuovi**? → Aggiungerli in `manuale/roadmap/backlog.md`
- **Errori o pattern da evitare**? → Aggiornare `manuale/regia_ai/errori_appresi.md` come ERR-[N+1]
  - Se aggiunti nuovi ERR-*: invocare `/orbit-skill-improver` nella prossima sessione

### 6. Conferma chiusura

Dichiara: "Sessione chiusa. File aggiornati: [lista file toccati]."

### 7. Push su GitHub (SEMPRE — ultimo step)

Esegui con il tool Bash:

```bash
BRANCH=$(git branch --show-current)
STAMP=$(date '+%d%m%y.%H%M' 2>/dev/null || powershell -Command "Get-Date -Format 'ddMMyy.HHmm'")
git add -A && git commit -m "Update $STAMP" && git push origin $BRANCH
```

- Se non ci sono modifiche (`nothing to commit`): eseguire solo `git push origin $BRANCH`
- Se il push fallisce per divergenza: segnalare — potrebbe esserci lavoro dall'altra macchina da scaricare prima
- Se il push va a buon fine: dichiarare "Push completato: Update [STAMP]"

> **Nota cross-platform**: questo comando funziona sia su Windows (Git Bash) che su macOS.
> Il fallback `powershell` per la data si attiva solo su Windows se `date` non è disponibile.
