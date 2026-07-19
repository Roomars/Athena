---
name: pipeline-cicd
description: Pattern per pipeline CI/CD: test automatici, build, deploy su ambienti multipli, gestione secrets, rollback. Usa quando configuri GitHub Actions, GitLab CI o qualsiasi pipeline di deploy.
---

# Pipeline CI/CD

Struttura e pattern per pipeline di integrazione e deploy continuo affidabili.

## Struttura pipeline standard

```
Push codice
  → Lint e type check        (veloce, blocca subito se c'è un errore ovvio)
  → Test unitari             (feedback rapido)
  → Build                    (verifica che compili)
  → Test integrazione        (più lento, solo su branch principali)
  → Deploy staging           (automatico su merge in main)
  → Test e2e su staging      (verifica comportamento reale)
  → Deploy produzione        (manuale o automatico con approvazione)
```

## Ambienti

| Ambiente | Trigger deploy | Approvazione |
|---|---|---|
| Development | Ogni push su branch feature | No |
| Staging | Merge in `main` | No |
| Produzione | Tag release o approvazione manuale | Sì |

## Gestione secrets

- Mai secrets nel codice o nei log
- Usa sempre variabili d'ambiente del provider CI
- Secrets diversi per ambiente — mai condividere prod/staging
- Ruota i secrets periodicamente

## Regole pratiche

- La pipeline deve completarsi in meno di 10 minuti — oltre è troppo lenta
- Un fallimento blocca il deploy — mai bypassare con `--force`
- Ogni step deve essere idempotente — può girare più volte senza danni
- Notifica sempre in caso di fallimento su `main` o produzione

## Rollback

- Ogni deploy deve avere una procedura di rollback documentata
- Il rollback deve essere eseguibile in meno di 5 minuti
- Testa il rollback periodicamente — non solo quando serve

## GitHub Actions — struttura base

```yaml
name: CI/CD
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  verifica:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
      - name: Test
      - name: Build

  deploy-staging:
    needs: verifica
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy su staging

  deploy-produzione:
    needs: deploy-staging
    environment: produzione   # richiede approvazione manuale
    steps:
      - name: Deploy su produzione
```
