---
name: checklist-sicurezza
description: Checklist pratica OWASP Top 10 per applicazioni web. Usa durante code review di sicurezza, prima di un deploy in produzione, o quando progetti meccanismi di autenticazione e autorizzazione.
---

# Checklist Sicurezza — OWASP Top 10

Verifica pratica delle vulnerabilità più comuni nelle applicazioni web.

## 1. Injection (SQL, NoSQL, Command)

- [ ] Input utente mai concatenato direttamente nelle query
- [ ] Query parametrizzate o ORM ovunque
- [ ] Input sanitizzato prima di passarlo a shell o OS

```sql
-- VIETATO
SELECT * FROM utenti WHERE email = '" + email + "'

-- CORRETTO
SELECT * FROM utenti WHERE email = $1
```

## 2. Autenticazione

- [ ] Password hashate con bcrypt/argon2 (mai MD5/SHA1)
- [ ] Rate limiting su login (max 5-10 tentativi)
- [ ] Token di sessione lunghi e casuali (min 128 bit)
- [ ] Logout invalida il token lato server
- [ ] HTTPS obbligatorio

## 3. Esposizione dati sensibili

- [ ] Dati sensibili cifrati a riposo (password, carte, dati sanitari)
- [ ] HTTPS su tutte le comunicazioni
- [ ] Nessun dato sensibile nei log
- [ ] Nessun segreto nel codice o nel repository

## 4. Controllo accessi

- [ ] Ogni endpoint verifica autenticazione E autorizzazione
- [ ] Utente non può accedere a risorse di altri utenti
- [ ] Admin route protette separatamente
- [ ] Principio del minimo privilegio

## 5. Security Misconfiguration

- [ ] Errori di produzione non espongono stack trace
- [ ] Header di sicurezza configurati (CSP, HSTS, X-Frame-Options)
- [ ] Directory listing disabilitato
- [ ] Credenziali di default cambiate

## 6. Cross-Site Scripting (XSS)

- [ ] Output utente sempre escaped/sanitizzato nell'HTML
- [ ] Content-Security-Policy configurato
- [ ] HttpOnly e Secure sui cookie di sessione

## 7. Dipendenze vulnerabili

- [ ] `npm audit` o equivalente eseguito regolarmente
- [ ] Dipendenze aggiornate (almeno security patch)
- [ ] Nessuna dipendenza abbandonata per funzionalità critiche

## 8. Logging e monitoraggio

- [ ] Login falliti loggati
- [ ] Accessi a dati sensibili loggati
- [ ] Log non contengono dati sensibili (password, token)
- [ ] Alert su anomalie (es. troppi 401 in poco tempo)

## 9. CSRF

- [ ] Token CSRF su tutte le form che modificano dati
- [ ] O utilizzo di SameSite=Strict sui cookie

## 10. Upload file

- [ ] Tipo file verificato lato server (non solo estensione)
- [ ] File salvati fuori dalla web root
- [ ] Nome file sanitizzato (no path traversal)
- [ ] Dimensione massima imposta

---

## Severità rapida

| Colore | Descrizione | Azione |
|---|---|---|
| Critica | Esecuzione codice, bypass auth totale | Blocca tutto, correggi subito |
| Alta | Accesso dati altrui, SQL injection | Correggi prima del deploy |
| Media | XSS, CSRF, info disclosure | Correggi nel prossimo sprint |
| Bassa | Header mancanti, log insufficienti | Backlog |
