# Ufficio di Programmazione — Agenti

> Fonte di verità: `CLAUDE.md`
> In caso di conflitto: `CLAUDE.md` prevale sempre.

---

## Flusso standard per una nuova feature

```
Obiettivo
  ↓
interroga-progetto   (se obiettivo vago)
  ↓
spec-feature         (se feature nuova o complessa)
  ↓
Orchestratore        propone piano → conferma utente
  ↓
sviluppo-sottoagenti (se 3+ task)
  ↓
Reviewer             code review + checklist-sicurezza
  ↓
Risultato + sessione.md aggiornato
```

---

## Orchestratore

Punto di ingresso unico. Non scrive codice — coordina.

---

## Agenti Core

| Agente | Ruolo | Modello |
|---|---|---|
| `architetto` | Struttura, tecnologie, decisioni, ADR | Opus |
| `frontend` | Componenti, pagine, routing, stato client | Sonnet |
| `backend` | API, logica server, autenticazione | Sonnet |
| `database` | Schema, migration, query, ottimizzazione | Sonnet |
| `ui-design` | Token CSS, layout, responsive, WCAG | Sonnet |
| `qa-tester` | Test unitari, integrazione, e2e | Sonnet |
| `reviewer` | Code review, sicurezza, qualità | Haiku |

## Specialisti

| Agente | Quando serve | Modello |
|---|---|---|
| `devops` | Deploy, CI/CD, ambienti | Sonnet |
| `security` | Audit sicurezza, OWASP | Opus |
| `ai-engineer` | LLM, prompt, pipeline AI | Opus |
| `business-analyst` | Requisiti vaghi | Haiku |
| `game-designer` | Progetti con gioco | Opus |
| `mobile` | App mobile native | Sonnet |
| `liveops` | Prodotti live | Haiku |
