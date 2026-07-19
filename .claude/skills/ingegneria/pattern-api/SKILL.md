---
name: pattern-api
description: Best practice per la progettazione di API REST: struttura endpoint, codici di stato, gestione errori, validazione input, versioning, paginazione. Usa quando progetti o revisioni un'API.
---

# Pattern API

Linee guida operative per API REST coerenti, sicure e manutenibili.

## Struttura endpoint

- Nomi risorse al plurale e in minuscolo: `/utenti`, `/ordini`, `/prodotti`
- Gerarchia per relazioni: `/utenti/{id}/ordini`
- Azioni non-CRUD come sotto-risorse: `/ordini/{id}/annulla`
- Versioning nel path: `/v1/utenti`

## Metodi HTTP

| Metodo | Uso | Idempotente |
|---|---|---|
| GET | Lettura | Sì |
| POST | Creazione | No |
| PUT | Sostituzione completa | Sì |
| PATCH | Modifica parziale | No |
| DELETE | Eliminazione | Sì |

## Codici di stato

| Codice | Quando usarlo |
|---|---|
| 200 | Successo con body |
| 201 | Risorsa creata |
| 204 | Successo senza body |
| 400 | Input non valido (errore client) |
| 401 | Non autenticato |
| 403 | Non autorizzato |
| 404 | Risorsa non trovata |
| 409 | Conflitto (es. duplicato) |
| 422 | Validazione fallita |
| 500 | Errore server |

## Struttura risposta errore

```json
{
  "errore": "CODICE_ERRORE",
  "messaggio": "Descrizione leggibile",
  "dettagli": [
    { "campo": "email", "problema": "formato non valido" }
  ]
}
```

## Validazione input

- Valida sempre al boundary (mai fidarsi del client)
- Restituisci tutti gli errori di validazione in una volta, non uno alla volta
- Sanitizza prima di salvare, valida prima di processare

## Paginazione

```json
{
  "dati": [...],
  "paginazione": {
    "pagina": 1,
    "per_pagina": 20,
    "totale": 150,
    "pagine": 8
  }
}
```

## Regole generali

- Ogni endpoint fa una cosa sola
- Risposte consistenti — stesso formato in tutta l'API
- Mai esporre dettagli interni negli errori (stack trace, query SQL)
- Documenta ogni endpoint con: input, output, errori possibili
