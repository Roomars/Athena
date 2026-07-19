---
name: spec-feature
description: Trasforma un obiettivo confermato in una specifica tecnica completa e actionable. Produce il documento che tutti gli agenti useranno come riferimento durante l'implementazione. Usa dopo interroga-progetto e prima dell'Orchestratore.
---

# Spec Feature

Trasforma un obiettivo in una specifica tecnica che elimina ambiguità durante l'implementazione.

## Input richiesto

- Output confermato di `interroga-progetto`
- Accesso al codebase esistente (leggi prima di scrivere)

## Struttura della specifica

```markdown
# Spec: [Nome Feature]

Data: [DD-MM-AAAA]
Stato: BOZZA | CONFERMATA

## Obiettivo
[Una frase. Cosa fa e per chi.]

## User Stories
- Come [ruolo] voglio [azione] così da [beneficio]
- ...

## Criteri di accettazione
- [ ] [Condizione verificabile — sì/no, non interpretabile]
- [ ] ...

## Architettura

### Componenti coinvolti
- [componente]: [cosa cambia]

### Flusso dati
[Input] → [elaborazione] → [output]

### Schema DB (se applicabile)
- Tabelle nuove: [lista]
- Tabelle modificate: [lista + modifiche]

### API (se applicabile)
- `POST /risorsa` — [descrizione]
- `GET /risorsa/{id}` — [descrizione]

## UI (se applicabile)
- [Pagina/componente]: [comportamento atteso]
- Stati da gestire: loading / errore / vuoto / dati

## Casi limite
- [Caso]: [comportamento atteso]
- ...

## Fuori scope
- [Cosa esplicitamente non fa questa feature]

## Dipendenze
- [Feature o componente che deve esistere prima]

## Rischi tecnici
- [Rischio]: [mitigazione]

## Stima agenti necessari
- [Agente]: [cosa farà]
```

## Comportamento

1. Leggi i file rilevanti del codebase prima di scrivere la spec
2. Sii specifico sui criteri di accettazione — devono essere verificabili
3. I casi limite sono obbligatori — almeno 3
4. Salva la spec in `docs/spec-[nome-feature].md`
5. Chiedi conferma prima di passarla all'Orchestratore

## Regola d'oro

Se un criterio di accettazione può essere interpretato in due modi, riscrivilo finché non è inequivocabile.
