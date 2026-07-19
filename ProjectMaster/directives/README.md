# Directive Layer

Questo layer contiene le **regole operative e di business** del progetto corrente.

I file qui dentro definiscono il "cosa" — le istruzioni che guidano gli agenti su vincoli,
politiche di dominio, requisiti non negoziabili e task operativi ricorrenti.

---

## Struttura

```
directives/
├── README.md               ← questo file
├── _template.md            ← template per creare nuove direttive
└── examples/
    └── business-rules.md   ← esempio di regole di business
```

---

## Come usare questo layer

1. **Crea un file per ogni area di business** — autenticazione, pagamenti, notifiche, ecc.
2. **Usa il template `_template.md`** come punto di partenza
3. **Non mettere qui codice** — solo regole, vincoli, decisioni di dominio
4. **Riferisci le direttive nel piano** — l'Orchestratore legge questa cartella prima di proporre un piano

---

## Relazione con gli altri layer

| Layer | File | Ruolo |
|---|---|---|
| **Directive** | `directives/*.md` | Cosa fare, regole, vincoli di dominio |
| **Orchestration** | `orchestration/` | Come coordinare, stato, piano di esecuzione |
| **Execution** | `execution/` | Come eseguire, script deterministici |

---

## Regola critica

I file in `directives/` sono **read-only per gli agenti di implementazione** (frontend, backend, database).
Solo l'Orchestratore e l'Architetto possono proporre modifiche alle direttive — e solo con conferma esplicita dell'utente.
