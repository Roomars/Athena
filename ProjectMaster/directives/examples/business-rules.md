# Direttiva: Regole di Business — Esempio

> **Stato:** esempio (non usare in produzione)
> **Ultima revisione:** 14-06-2026

---

## Scopo

Questo file mostra come documentare le regole di business di un progetto.
Copiare e adattare per il progetto reale.

---

## Autenticazione e Accesso

### R1 — Sessione utente
- Durata massima sessione: 7 giorni per utenti normali, 24h per admin
- Refresh token automatico se la sessione scade entro 30 minuti
- Mai memorizzare token in localStorage — usare httpOnly cookie

### R2 — Permessi
- Struttura RBAC: `admin`, `editor`, `viewer`
- Le operazioni distruttive (delete, archive) richiedono ruolo `admin`
- Gli `editor` possono creare e modificare, non eliminare

---

## Dati e Privacy

### R3 — Dati personali
- I dati PII non devono apparire nei log di applicazione
- Email e telefono: sempre cifrati a riposo nel database
- Cancellazione account: hard delete entro 30 giorni dalla richiesta (GDPR)

### R4 — Audit trail
- Ogni modifica a dati critici deve essere registrata con: chi, quando, cosa
- I log di audit sono immutabili — nessun `UPDATE` o `DELETE` sulla tabella audit

---

## Pagamenti

### R5 — Transazioni
- Mai processare pagamenti lato client — sempre server-side
- Ogni transazione deve avere idempotency key per evitare duplicati
- In caso di errore: fail fast, non tentare retry automatici oltre 3 volte
