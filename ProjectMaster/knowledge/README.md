# Knowledge Hub — Single Source of Truth

Questa cartella è il **cervello documentale del progetto**.
Prima di scrivere una riga di codice, ogni agente legge questa cartella.
Nessuna specifica viene inventata: se non è qui, non esiste.

---

## Struttura

```
knowledge/
├── README.md               ← questo file
├── PRD.md                  ← Product Requirements Document (requisiti funzionali)
├── api_specs.json          ← Specifiche API (endpoint, payload, auth)
├── data_model.md           ← Schema dati, entità, relazioni
└── style_guide.md          ← Convenzioni di codice, naming, formatting
```

Aggiungi file in base al progetto. Ogni file è una fonte di verità per un dominio specifico.

---

## Regola di utilizzo (RAG Protocol)

1. **All'avvio di ogni task** — l'Orchestratore elenca i file presenti e identifica quali sono rilevanti
2. **Durante la pianificazione** — i requisiti nel piano devono citare la fonte in `/knowledge`
3. **Durante l'implementazione** — se un agente incontra un'ambiguità, cerca prima qui. Solo se la risposta non è trovata, chiede all'utente
4. **Durante la review** — il Reviewer verifica che il codice sia allineato ai documenti di questa cartella

---

## Come mantenere questa cartella

| File | Chi lo aggiorna | Quando |
|---|---|---|
| `PRD.md` | Utente | Quando cambiano i requisiti funzionali |
| `api_specs.json` | Utente + Architetto | Quando si aggiungono/cambiano endpoint |
| `data_model.md` | Architetto + Database | Dopo ogni migrazione significativa |
| `style_guide.md` | Utente | All'inizio del progetto, raramente dopo |

---

## Priorità di lettura

In caso di conflitto tra documenti:

```
knowledge/ > directives/ > CLAUDE.md > output degli agenti
```

I documenti in `/knowledge` hanno sempre la precedenza su qualsiasi altra fonte.
