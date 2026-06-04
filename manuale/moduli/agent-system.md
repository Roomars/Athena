# Modulo: Agent System

**Stato:** roadmap FASE 4  
**Cartella prevista:** `modules/agents/`  
**Aggiornato:** 04-06-2026

---

## Concetto

Gli agenti permettono ad Athena di eseguire azioni reali sul sistema (file, shell, ricerca). Ogni azione è tracciata, ogni azione distruttiva richiede conferma. Nessun agente opera senza supervisione di Roby.

---

## Agenti previsti

### Agent File
- Legge file dal filesystem di Roby
- Scrive/modifica file (con backup automatico obbligatorio prima)
- Crea cartelle, lista contenuti directory

### Agent Shell
- Esegue comandi nel terminale
- Richiede **doppia conferma** per comandi distruttivi
- Log completo di ogni comando eseguito
- Non esegue mai comandi in background senza notifica

### Agent Search (futuro)
- Ricerca nel web (con motore da definire)
- Ricerca nelle note Brain (ChromaDB)
- Ricerca nei file locali

---

## Regole inviolabili per tutti gli agenti

1. Nessuna azione senza conferma esplicita di Roby
2. Prima di modificare/eliminare file → backup in `backups/`
3. Log di ogni azione in `self/changelog.md`
4. In caso di errore → rollback automatico + notifica

---

## Flusso esecuzione agente

```
Athena propone azione
        ↓
[se modifica file] → backup automatico
        ↓
Mostra a Roby: cosa farà + quali file toccherà
        ↓
Roby conferma → esegue
Roby nega → annulla, spiega
        ↓
Risultato → mostrato a Roby
        ↓
Log in self/changelog.md
```
