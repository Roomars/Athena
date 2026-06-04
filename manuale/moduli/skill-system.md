# Modulo: Skill System

**Stato:** roadmap FASE 3  
**Cartella prevista:** `modules/skills/`  
**Aggiornato:** 04-06-2026

---

## Concetto

Una Skill è un file `SKILL.md` con istruzioni comportamentali che modificano il modo in cui Athena risponde in un contesto specifico. Skill attive → incluse nel system prompt.

Esempi di skill:
- `tactical-lab` — analisi strategica, pensiero strutturato
- `psychology` — ascolto attivo, domande aperte
- `coding` — revisione codice, debug guidato

---

## Componenti previsti

| Componente | Funzione |
|---|---|
| Skill Loader | Carica i file `SKILL.md` dalla cartella skills/ |
| Skill Coach | Skill predefinite sempre disponibili |
| Skill Selector | UI nella sidebar per attivare/disattivare skill |
| Skill Creator | Athena aiuta Roby a creare nuove skill interattivamente |

---

## Formato SKILL.md (bozza)

```markdown
# Skill: [Nome]
**Trigger:** [keyword o contesto]
**Descrizione:** [cosa fa questa skill]

## Istruzioni per Athena
[istruzioni in linguaggio naturale che Athena incorpora nel comportamento]
```

---

## Da definire in fase di progettazione

- Come il Skill Loader inietta le skill nel system prompt (append? replace?)
- Limite di skill attivabili contemporaneamente
- Persistenza della skill attiva tra sessioni
