# Orchestration Layer

Questo layer gestisce **come il lavoro viene coordinato** e **lo stato del progetto nel tempo**.

Contiene tre componenti:
1. **State management** a 3 tier — dove si trova la conoscenza del progetto
2. **Plans** — piani di task generati prima di scrivere codice
3. **Configurazione agenti** — delegata a `.claude/agents/` (source of truth)

---

## Struttura

```
orchestration/
├── README.md               ← questo file
├── state/
│   ├── ephemeral.md        ← stato temporaneo della sessione corrente
│   ├── journal.md          ← log append-only di tutte le azioni (permanente)
│   └── canonical.md        ← architettura e decisioni stabili (versioned)
└── plans/
    ├── _template.json      ← template per nuovi piani
    └── [AAAA-MM-DD]-[slug].json  ← piani storici
```

---

## I 3 Tier di Stato

### Ephemeral (temporaneo)
**File:** `state/ephemeral.md`
**Vita:** Una sessione di lavoro. Si azzera all'inizio di ogni sessione.
**Contiene:** obiettivo sessione, task in corso, variabili temporanee, note rapide.
**Chi scrive:** Orchestratore all'apertura e chiusura sessione.

### Journal (cronologico)
**File:** `state/journal.md`
**Vita:** Permanente — append-only, niente viene mai cancellato.
**Contiene:** log di ogni azione completata con timestamp, agente, esito.
**Chi scrive:** Orchestratore dopo ogni task completato.

### Canonical (stabile)
**File:** `state/canonical.md`
**Vita:** Permanente — aggiornato solo quando una decisione è stabilizzata.
**Contiene:** stack tecnologico, ADR, architettura, versione stabile.
**Chi scrive:** Architetto (con conferma utente), mai in autonomia.

---

## Regole di confine

| Livello | Chi può scrivere | Quando |
|---|---|---|
| Ephemeral | Orchestratore | Apertura/chiusura sessione, aggiornamenti stato |
| Journal | Orchestratore | Dopo ogni task completato |
| Canonical | Architetto + conferma utente | Solo su decisioni stabilizzate |

**Regola critica:** Non mescolare tier. Lo stato canonico non viene mai modificato durante una sessione di implementazione attiva — solo dopo review e conferma.

---

## Plans

Prima di iniziare qualsiasi task con 2+ agenti, l'Orchestratore genera un file `plans/[data]-[slug].json` usando il template `_template.json`. Il codice non viene toccato finché il piano non è approvato.
