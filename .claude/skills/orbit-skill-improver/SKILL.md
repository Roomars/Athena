---
name: orbit-skill-improver
description: >
  Aggiornamento continuo delle skill Orbit. Legge errori_appresi.md, identifica gap
  nelle skill esistenti, propone regole aggiuntive con riferimento ERR-*, aggiorna
  le skill dopo conferma utente. Invocare quando vengono catalogati nuovi ERR-*.
model: claude-sonnet-4-6
---

# Orbit Skill Improver

> *Le skill crescono con il progetto. Ogni errore imparato diventa una regola permanente.*

---

## Scopo

Le skill di Orbit non sono statiche. Ogni volta che viene catalogato un nuovo ERR-* in `manuale/regia_ai/errori_appresi.md`, questa skill valuta se quel pattern è già coperto da una regola esistente o se va aggiunto come nuova regola a una skill.

L'obiettivo è che ogni errore fatto una volta non venga mai ripetuto — non perché lo ricordiamo, ma perché la skill lo blocca automaticamente.

---

## EXECUTION — Procedura di miglioramento

### Passo 1 — Leggi gli errori appresi

Leggi con il tool Read: `manuale/regia_ai/errori_appresi.md`

Per ogni ERR-* presente, annota:
- Il pattern errato
- La skill più pertinente che dovrebbe bloccarlo
- Se la skill già copre questo pattern (CHECK-3 in orbit-code-guard o regola in un agente)

### Passo 2 — Identifica i gap

Per ogni ERR-* non ancora coperto da nessuna skill:

1. Identificare quale skill deve essere aggiornata:
   - Pattern di codice Python → `orbit-code-guard` (CHECK-3)
   - Comportamento architetturale → agente `core/architetto.md`
   - Pattern di test → agente `core/qa-engineer.md`
   - Pattern di documentazione → agente `core/tech-writer.md`
   - Pattern di build → agente `core/build-engineer.md`

2. Formulare la regola da aggiungere nel formato:

```
| ERR-[N] | [descrizione breve del pattern da bloccare] |
```

### Passo 3 — Proponi le modifiche

Prima di toccare qualsiasi file, presenta all'utente:

```
📋 SKILL IMPROVER — Proposte di aggiornamento

ERR-[N] → [nome skill da aggiornare]
  Pattern attuale: [non coperto / coperto parzialmente]
  Regola proposta: [descrizione della regola da aggiungere]
  Sezione da aggiornare: [CHECK-N o sezione specifica]

Confermo le modifiche? (sì / modifica / salta)
```

Una proposta alla volta se ci sono più ERR-* da processare.

### Passo 4 — Applica dopo conferma

Solo dopo conferma esplicita dell'utente:

1. Leggi il file della skill con Read
2. Aggiungi la riga nella tabella appropriata con Edit
3. Verifica che la modifica sia coerente con le regole esistenti

**Regola**: mai modificare il tono o la struttura della skill — solo aggiungere righe nelle tabelle o nella checklist esistenti.

### Passo 5 — Conferma

Dichiara: "Skill [nome] aggiornata con ERR-[N]. Regola aggiunta: [descrizione]."

---

## Quando invocarmi

- Vengono aggiunti uno o più ERR-* nuovi a `errori_appresi.md`
- Si sospetta che una skill non stia coprendo un tipo di errore ricorrente
- Si vuole fare un audit periodico delle skill rispetto agli errori accumulati
- Si inizia lo sviluppo di un nuovo modulo e si vogliono pre-caricare regole specifiche

---

## Regole che non violo mai

- Non modifico una skill senza leggere prima il file completo
- Non cambio regole esistenti — solo aggiungo
- Non aggiungo regole senza una conferma esplicita dell'utente
- Non cancello ERR-* da `errori_appresi.md` — è append-only
