---
name: sviluppo-sottoagenti
description: Esegue un piano di implementazione spezzandolo in task isolati, ognuno delegato a un sottoagente con contesto pulito. Evita che i task precedenti inquinino quelli successivi. Usa quando l'Orchestratore ha un piano con 3+ task indipendenti.
---

# Sviluppo con Sottoagenti

Esegui piani complessi mantenendo il contesto pulito per ogni task.

## Quando usare

- Piano con 3 o più task indipendenti
- Task che possono andare in parallelo
- Feature complesse dove il contesto accumulato potrebbe creare confusione

## Procedura

### Fase 1 — Decomposizione

Ricevi il piano dall'Orchestratore. Spezzalo in task atomici:

**Regole di decomposizione:**
- Ogni task produce un output verificabile
- Ogni task è indipendente dagli altri (o le dipendenze sono esplicite)
- Ogni task ha un solo agente responsabile
- Nessun task dura più di 30 minuti stimati

**Formato task:**
```
Task N: [nome]
Agente: [agente responsabile]
Input: [cosa riceve]
Output: [cosa produce]
Dipende da: [task N-1, o "nessuno"]
```

### Fase 2 — Esecuzione isolata

Per ogni task, in ordine di dipendenze:

1. **Prepara il contesto** — passa al sottoagente solo ciò che serve per quel task specifico
2. **Esegui** — il sottoagente lavora con contesto pulito
3. **Verifica output** — controlla che l'output corrisponda a quanto atteso
4. **Passa al successivo** — usa l'output come input del task dipendente

**Regola critica:** non passare l'intera conversazione al sottoagente — solo spec, file rilevanti, e output dei task precedenti da cui dipende.

### Fase 3 — Review parallela

Dopo ogni task completato, il Reviewer legge solo quel task (non l'intero progetto).

### Fase 4 — Integrazione

Quando tutti i task sono completati:
1. Verifica che gli output si integrino correttamente
2. Esegui i test sull'insieme
3. Riporta il risultato all'Orchestratore

## Vantaggi

- Contesto pulito → meno errori da "ricordi" precedenti
- Parallelizzabile → task indipendenti girano insieme
- Review mirata → ogni task è verificato isolatamente
- Rollback semplice → se un task fallisce, gli altri non sono compromessi
