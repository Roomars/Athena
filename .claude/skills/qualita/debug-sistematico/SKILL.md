---
name: debug-sistematico
description: Processo strutturato per diagnosticare e risolvere bug. Ipotesi → verifica → conclusione. Evita il debug per tentativi casuali. Usa quando un bug non è immediatamente ovvio o quando i tentativi precedenti non hanno funzionato.
---

# Debug Sistematico

Diagnostica i bug con metodo, non per tentativi.

## Principio

Un bug è sempre causato da un'assunzione sbagliata. Il debug è il processo di trovare quale assunzione è sbagliata.

## Procedura

### Fase 1 — Descrivi il problema

Prima di toccare il codice, rispondi a:

```
Comportamento atteso: [cosa dovrebbe succedere]
Comportamento reale:  [cosa succede invece]
Quando si manifesta: [sempre / in certi casi / intermittente]
Quando è iniziato:   [dopo quale cambiamento, se noto]
```

### Fase 2 — Raccogli prove

Leggi (non modificare ancora):
- Il messaggio di errore completo e lo stack trace
- Il codice nel punto dell'errore e i suoi chiamanti
- I log rilevanti
- I test esistenti per quella funzionalità

### Fase 3 — Formula ipotesi

Elenca le possibili cause, dalla più probabile alla meno probabile:

```
Ipotesi 1: [causa] — probabilità: alta/media/bassa
  Verifica: [come controllare se è questa]
  
Ipotesi 2: [causa] — probabilità: alta/media/bassa
  Verifica: [come controllare se è questa]
```

**Regola:** massimo 3 ipotesi. Se ne hai di più, le prime 3 sono abbastanza.

### Fase 4 — Verifica in ordine

Parti dall'ipotesi più probabile. Per ogni ipotesi:

1. Aggiungi un punto di osservazione (log, breakpoint, test)
2. Esegui
3. Leggi il risultato
4. Concludi: confermata / esclusa / nuova informazione

**Non correggere nulla finché non hai identificato la causa.**

### Fase 5 — Correggi

Solo quando la causa è identificata con certezza:

1. Scrivi la correzione minima che risolve il problema
2. Verifica che il bug sia risolto
3. Verifica che nulla di esistente sia rotto
4. Aggiungi un test che avrebbe catturato il bug originale

### Fase 6 — Documenta

```
Bug: [descrizione in una riga]
Causa: [assunzione sbagliata che lo generava]
Correzione: [cosa è cambiato]
Test aggiunto: [sì/no — se no, perché]
```

## Segnali di allarme durante il debug

- Stai modificando codice senza capire perché dovrebbe funzionare → fermati
- Hai fatto 3+ tentativi senza successo → ricomincia dalla Fase 1
- Il bug scompare senza una spiegazione chiara → non è risolto, è nascosto
- La correzione richiede più di 20 righe → probabilmente stai correggendo il sintomo, non la causa
