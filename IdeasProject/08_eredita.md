# Athena — Cosa prendere da athenaOld

## Principio

Ripensato da zero significa: nessuna dipendenza strutturale dal vecchio codice.
Ma il vecchio codice contiene idee valide che non vanno reimplementare da zero.
Copiamo solo ciò che è corretto, ben pensato, e non richiede riscrittura.

---

## COPIA DIRETTA (file da portare as-is o con modifiche minime)

### athena.md — Costituzione
**Stato:** Ottima. Carattere, regole operative, system prompt — tutto corretto.
**Azione:** Copia in `/IdeasProject/riferimenti/athena_constitution.md`
**Modifiche:** Aggiornare sezione "Capacità attuali" con il nuovo stack.

### roby.md — Profilo utente
**Stato:** Buono. Contiene info su Roby accumulate nel tempo.
**Azione:** Copia in `/vault/roby/profilo.md` (Obsidian vault)
**Modifiche:** Rimuovere riferimenti a versioni specifiche del vecchio stack.

### manuale/architettura/decisioni.md — DEC-1..DEC-20
**Stato:** Documentazione preziosa. Molte DEC sono ancora valide come riferimento storico.
**Azione:** Copia in `/IdeasProject/riferimenti/decisioni_old.md`
**Uso:** Solo consultazione. Le nuove DEC vanno scritte da zero per Athena 2.0.
**Non importare ciecamente:** DEC-1 (Swift puro) è superata. DEC-2 (GRDB) superata.

---

## LOGICA DA RISCRIVERE IN PYTHON (non copia, concetto portato avanti)

### VaultChunker — chunking heading-aware
**Vecchio:** `VaultChunker.swift` — splittava documenti Obsidian preservando il path heading
**Nuovo:** `athena/memory/vault_chunker.py` — stessa logica, Python
**Perché riscrivere:** il concetto è ottimo, l'implementazione Swift non serve più

### Memory append-only con score decay
**Vecchio:** GRDB con campo `score` che decade nel tempo
**Nuovo:** ChromaDB con metadata `score` + `created_at` + `updated_at`
**Perché riscrivere:** database diverso, ma il principio (non cancellare, fare decay) rimane

### CodeRepairService — retry loop con max 3 tentativi
**Vecchio:** `CodeRepairService.swift` — ricompilava e ritentava fino a 3 volte
**Nuovo:** nella self-modification engine Python
**Perché riscrivere:** stessa logica, contesto diverso (Python + git invece di xcodebuild puro)

### Routing a tier (OnDevice/Local/Cloud)
**Vecchio:** `RouterService.swift` + `AdvancedRouter.swift` (incompleto)
**Nuovo:** `athena/core/router.py` — euristica + LLM router
**Perché riscrivere:** l'idea dei tier è giusta, l'implementazione era incompleta

### SkillManager con format YAML frontmatter
**Vecchio:** YAML frontmatter per metadata skill — ottima idea, compatibile con Claude Code
**Nuovo:** mantenere il formato YAML, cambiare il registry in Python
**Cosa portare:** il formato YAML, non il codice Swift

---

## SCARTARE COMPLETAMENTE

### GRDB layer
**Motivo:** Sostituito da ChromaDB + aiosqlite. Complessità non giustificata.

### GraphifyService (incompleto)
**Motivo:** Il grafo Obsidian serve da visualizzazione esterna. Non serve integrarlo nel codice.
Obsidian stesso visualizza il grafo. Athena scrive le note, Obsidian fa il grafo.

### FoundationModels / OnDevice Tier (Apple Intelligence)
**Motivo:** Richiede macOS 15.2+, modelli Apple piccoli, dipendenza da framework ancora instabile.
Da rivalutare in futuro se Apple Intelligence migliora.

### BrainSearch (scritto ma non iniettato)
**Motivo:** Era ChromaDB-like in Swift. Refactoring completo in Python è più pulito.

### AthenaOS.xcodeproj struttura attuale
**Motivo:** Rebuild da zero con struttura più chiara. La vecchia ha accumulato refactoring incompleti.

### helpers/think.py
**Motivo:** Loop di ragionamento iterativo — interessante come idea ma il nuovo LLM (32B) non ne ha bisogno per la maggior parte dei task. Da rivalutare solo se serve Chain-of-Thought esplicito.

---

## RIFERIMENTI DA TENERE A PORTATA

Questi file non vengono copiati nel progetto ma vanno consultati durante sviluppo:

- `athenaOld/manuale/architettura/stack.md` — confronto modelli testati
- `athenaOld/manuale/moduli/cervello.md` — dettaglio 4 livelli memoria (ben documentato)
- `athenaOld/manuale/moduli/skill-system.md` — ciclo vita skills (ancora valido concettualmente)
- `athenaOld/manuale/roadmap/` — roadmap e backlog (per non dimenticare feature già pianificate)

---

## Struttura nuova cartella progetto

```
/Users/roby/Documents/Athena/
├── IdeasProject/           ← documenti di progettazione (questo repo)
├── AthenaUI/               ← Swift/SwiftUI app (nuovo, da creare)
├── athena/                 ← Python daemon (nuovo, da creare)
│   ├── core/
│   ├── memory/
│   ├── skills/
│   └── self_modify/
├── vault/                  ← Obsidian vault (knowledge base)
├── athenaOld/              ← archivio vecchia versione (non toccare)
└── piper/                  ← TTS alternativo (valutare se serve)
```
