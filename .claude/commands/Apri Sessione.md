---
allowed-tools: Read, Bash
description: Apertura sessione — sync git, health check, stato progetto e obiettivo
---

# Apri Sessione

## Info sessione

- Data/ora: !`date "+%d-%m-%Y - %H:%M"`
- Branch attivo: !`git branch --show-current`

## Step 1 — Sync automatico

```bash
git pull origin $(git branch --show-current) --rebase
```

Se il pull fallisce per conflitti: segnalarlo e fermarsi.
Se va a buon fine: proseguire silenziosamente.

## Step 2 — Health check

Esegui in parallelo:

```bash
echo "=BRANCH=" && git branch --show-current
echo "=DIRTY=" && git status --short | wc -l | tr -d ' '
echo "=AHEAD/BEHIND=" && git rev-list --count --left-right HEAD...origin/$(git branch --show-current) 2>/dev/null || echo "n/a"
```

Presenta i risultati in questo formato:

```
Health Check
• Git: branch [nome], [N] file modificati non committati, [X] ahead / [Y] behind
```

## Step 3 — Stato progetto

Leggi con il tool Read: `sessione.md`

Se il file non esiste: crearlo con il template minimo (vedi sotto) e proseguire.

Dichiara:
1. Ultimo lavoro completato
2. Blockers attivi (se presenti)
3. Prossime priorità (max 3)

Poi chiedi: "Qual è l'obiettivo di questa sessione?"

---

### Template `sessione.md` (solo se non esiste)

```markdown
# Stato sessione

## Ultimo aggiornamento
<!-- data/ora -->

## Lavoro corrente
<!-- descrizione sintetica -->

## Prossime priorità
1. 
2. 
3. 

## Blocker attivi
<!-- nessuno -->

## Changelog
<!-- - DD-MM-AAAA HH:mm: descrizione -->
```
