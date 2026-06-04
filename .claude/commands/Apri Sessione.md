---
allowed-tools: Read, Bash
description: Apertura sessione Orbit Desktop — sync git da GitHub, health check Python, stato progetto e obiettivo. Funziona su Windows e macOS.
---

# Apri Sessione

Esegui apertura sessione Orbit Desktop completa.

## Info sessione

- Data/ora corrente: !`date "+%d-%m-%Y - %H:%M" 2>/dev/null || powershell -Command "Get-Date -Format 'dd-MM-yyyy - HH:mm'"`
- Sistema operativo: !`uname -s 2>/dev/null || echo "Windows"`
- Branch attivo: !`git branch --show-current`

---

## Step 1 — Sync da GitHub (SEMPRE — prima di tutto)

Questo step garantisce che tu stia lavorando sull'ultima versione del codice,
indipendentemente da quale macchina hai usato l'ultima volta.

Esegui con il tool Bash:

```bash
git fetch origin && git pull origin $(git branch --show-current) --rebase
```

- Se il pull va a buon fine: proseguire silenziosamente
- Se ci sono **conflitti di rebase**: segnalare all'utente e fermarsi — non risolvere automaticamente
- Se il **remote non è raggiungibile**: segnalare con ⚠️ ma proseguire (si lavora offline)

---

## Step 2 — Health check progetto

Esegui questi check con il tool Bash. Sono **informativi** — non bloccano l'apertura.
Raccogli tutti i risultati e presentali in un unico blocco.

### Check 1 — Branch e stato git

```bash
echo "=BRANCH=" && git branch --show-current
echo "=AHEAD/BEHIND=" && git rev-list --count --left-right HEAD...origin/$(git branch --show-current) 2>/dev/null || echo "n/a"
echo "=DIRTY=" && git status --short | wc -l | tr -d ' '
```

Interpreta:
- `AHEAD`: commit locali non ancora pushati. Se > 0: ⚠️ ci sono modifiche da pushare.
- `BEHIND`: commit remoti non ancora scaricati. Se > 0 dopo il pull: ⚠️ conflitto non risolto.
- `DIRTY`: file modificati non committati. Se > 0: ⚠️ working tree sporco.

### Check 2 — Ambiente Python (cross-platform)

```bash
python --version 2>&1 || python3 --version 2>&1
python -c "import sys; print('venv: sì' if sys.prefix != sys.base_prefix else 'venv: no - attivare .venv')" 2>/dev/null || python3 -c "import sys; print('venv: sì' if sys.prefix != sys.base_prefix else 'venv: no - attivare .venv')" 2>/dev/null
```

Se Python non trovato: ⚠️ ambiente non configurato.
Se venv non attivo: ⚠️ ricordare all'utente di attivare `.venv`:
- Windows: `.venv\Scripts\activate`
- macOS: `source .venv/bin/activate`

### Check 3 — Dipendenze Python

```bash
pip check 2>&1 | tail -3
```

Se `No broken requirements`: ✅ dipendenze OK.
Se ci sono conflitti: ⚠️ suggerire `pip install -r requirements.txt`.

### Check 4 — Test suite

```bash
python -m pytest tests/ -q --tb=no 2>&1 | tail -3
```

Se tutti passano: ✅ suite verde.
Se ci sono fallimenti: ⚠️ mostrare conteggio e primi 2 test falliti.
Se `tests/` non esiste: segnalare senza bloccare.

### Output Health Check

```
🔍 Health Check — [Windows / macOS]
• Git:      ✅ branch main, 0 sporchi  (oppure ⚠️ dettaglio)
• Python:   ✅ 3.11 — venv attivo      (oppure ⚠️ dettaglio)
• Deps:     ✅ nessun conflitto        (oppure ⚠️ dettaglio)
• Test:     ✅ N passed                (oppure ⚠️ N failed — test: ...)
```

---

## Step 3 — Task interrotto (checkpoint)

Leggi `manuale/regia_ai/task_checkpoint.md` con il tool Read.

Se `status` è `IN_CORSO`:
- Mostrare: "**TASK INTERROTTO trovato**: [task] — [blocco corrente]"
- Chiedere: "Vuoi **continuare** questo task o **ignorarlo**?"
- Se continua: caricare il contesto del checkpoint come priorità sessione
- Se ignora: proseguire normalmente

Se `status` è `NESSUNO` o `COMPLETATO`: proseguire senza menzionarlo.

---

## Step 4 — Stato progetto

Leggi in parallelo con il tool Read:

1. `manuale/regia_ai/stato_sessione.md`
2. `manuale/regia_ai/errori_appresi.md`

Dichiara in modo conciso:

1. **Fase attiva** e stato corrente
2. **Ultimo lavoro completato**
3. **Blocker attivi** (se presenti)
4. **Prossime priorità** (max 3)
5. **Ultimi 3 errori** da non ripetere (se presenti)

Poi chiedi: "Qual è l'obiettivo di questa sessione?"
