---
name: <nome-skill>
description: <una riga — cosa fa, quando invocarla, contesto chiave>
license: proprietary
metadata:
  author: misterlab
  version: "1.0.0"
  last_updated: DD-MM-AAAA
---

# MisterLab — <Nome Skill>

## Core Differentiator

> Dichiara perché questa skill esiste e cosa la distingue da un prompt generico.
> Rispondere a: "Cosa fa questa skill che un agente senza skill non farebbe bene?"
> Max 3-4 righe. Leggibile in 10 secondi.

[Es. "Questa skill governa X. Senza di essa l'agente improvvisa su Y causando Z.
Con questa skill l'agente segue sempre il processo A→B→C e si ferma prima di D."]

---

## 1. PRIMACY — Chi sei e regole assolute

Sei [ruolo]. Il tuo compito: [missione in una riga].

**Modello consigliato:** `Haiku` / `Sonnet 4.6` / `Opus` — [motivazione breve]

**Regole che non si violano mai:**
- MAI [comportamento proibito] (ERR-NNN se applicabile)
- MAI [comportamento proibito]

**Stop conditions — fermarsi e chiedere prima di:**
- [Azione rischiosa 1]
- [Azione rischiosa 2]

---

## 2. Router — [Quale sotto-dominio / modalità?]

> Usare questa sezione quando la skill copre più sotto-domini o modalità distinte.
> Omettere se la skill ha un solo percorso.

| Segnali nel task | Sotto-dominio | Sezione |
| --- | --- | --- |
| [keyword / condizione] | [Nome sotto-dominio A] | §3 |
| [keyword / condizione] | [Nome sotto-dominio B] | §4 |

---

## 3. [Nome sotto-dominio A / Procedura principale]

### Trigger
[Cosa attiva questo percorso]

### Passi
1. [Passo 1 — attore + azione]
2. [Passo 2]
3. [...]

---

## 4. [Nome sotto-dominio B — se presente]

[...]

---

## 5. Qualità attesa

L'output è corretto quando:
- [Condizione misurabile 1 — non "funziona bene" ma criterio oggettivo]
- [Condizione misurabile 2]
- TypeScript PASS (`npx tsc --noEmit`) — se applicabile

---

## SUCCESS LOCK — L'esecuzione è completa quando

- [ ] [Condizione di processo verificabile]
- [ ] [Qualità attesa (§5) verificata]
- [ ] [Conferma utente se richiesta]

---

## Changelog

- DD-MM-AAAA v1.0.0: prima versione
