# Flusso: Athena Shell — Self Evolution

**Stato:** da implementare (FASE 6)  
**Aggiornato:** 04-06-2026

---

## Principio

Athena può proporre e implementare modifiche a se stessa. Il flusso è rigido e non saltabile. Senza conferma esplicita di Roby, non si muove.

---

## Flusso obbligatorio

```
1. OSSERVA    → identifica il problema o miglioramento
               (da pattern d'uso, da richiesta esplicita di Roby)

2. PROPONE    → descrive in chiaro:
               - cosa cambierà
               - quali file verranno toccati
               - perché
               → ASPETTA CONFERMA DI ROBY

3. BACKUP     → crea ~/Documents/athena/backups/YYYY-MM-DD_HH-MM/
               - copia tutti i file da modificare
               - scrive restore.md con comandi cp esatti

4. CHIEDE     → "Backup creato in [path]. Procedo?"
               → ASPETTA CONFERMA DI ROBY

5. IMPLEMENTA → modifica i file

6. VERIFICA   → controlla che il backend risponda (GET /)
               → segnala se qualcosa non va

7. RIPORTA    → mostra diff delle modifiche
               → conferma o propone rollback
               → aggiorna self/changelog.md
```

---

## File che richiedono DOPPIA conferma

- Eliminazione di qualsiasi file
- `core/app.py`
- `src-tauri/src/main.rs`
- Qualsiasi file in `backups/`

---

## Formato restore.md (obbligatorio nel backup)

```markdown
# Backup YYYY-MM-DD HH:MM
## Motivo modifica
[descrizione]

## File modificati
- core/memory.py
- static/index.html

## Come ripristinare
cp ~/Documents/athena/backups/YYYY-MM-DD_HH-MM/core/memory.py ~/Documents/athena/core/memory.py
cp ~/Documents/athena/backups/YYYY-MM-DD_HH-MM/static/index.html ~/Documents/athena/static/index.html

## Riavvia il backend
cd ~/Documents/athena && ./start.sh
```
