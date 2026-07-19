---
name: interroga-progetto
description: Intervista strutturata prima di qualsiasi implementazione. Claude fa domande una alla volta finché il piano non è inequivocabile. Usa SEMPRE prima di iniziare una feature nuova o un task complesso. Elimina il problema delle assunzioni sbagliate.
---

# Interroga Progetto

Prima di scrivere una riga di codice, raggiungi una comprensione condivisa e completa dell'obiettivo.

## Quando usare questa skill

- Inizio di qualsiasi feature non banale
- Obiettivo descritto in modo vago o incompleto
- Task che coinvolge più di 2 agenti
- Decisioni irreversibili (schema DB, architettura, API pubblica)

## Procedura

### Fase 1 — Ascolto

Ricevi l'obiettivo dell'utente. Non interrompere, non fare assunzioni, non proporre soluzioni.

### Fase 2 — Domande (una alla volta)

Fai domande in quest'ordine di priorità:

**Cosa:**
- Qual è il risultato finale visibile per l'utente?
- Come si capisce che è completato correttamente?
- Cosa succede se non viene fatto?

**Chi:**
- Chi usa questa funzionalità?
- Ci sono ruoli diversi con comportamenti diversi?

**Confini:**
- Cosa è esplicitamente fuori scope?
- Ci sono vincoli tecnici o di business?
- Ci sono dipendenze con funzionalità esistenti?

**Rischi:**
- Cosa potrebbe andare storto?
- Ci sono dati esistenti da preservare?
- È reversibile se qualcosa non va?

**Regola:** una domanda alla volta. Aspetta la risposta prima della prossima.
Fermati quando hai risposta a tutte le domande rilevanti — non fare domande inutili.

### Fase 3 — Riepilogo

Prima di passare all'Orchestratore, scrivi un riepilogo in questo formato:

```
OBIETTIVO: [una frase]

RISULTATO ATTESO: [cosa sarà diverso quando è fatto]

SCOPE:
- In scope: [lista]
- Fuori scope: [lista]

VINCOLI: [tecnici, di business, di tempo]

RISCHI: [cosa potrebbe complicare le cose]

ASSUNZIONI: [ciò che diamo per scontato]
```

Chiedi conferma esplicita: "È corretto? Possiamo procedere?"

### Fase 4 — Passa all'Orchestratore

Solo dopo conferma, passa il riepilogo all'Orchestratore come input per la pianificazione.
