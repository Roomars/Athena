# Athena — Cervello e Memoria

## Quattro livelli di memoria

```
┌─────────────────────────────────────────────┐
│  WORKING MEMORY                              │
│  Conversazione corrente (array in RAM)       │
│  Si azzera a fine sessione                   │
│  Max ~20 messaggi (sliding window)           │
└─────────────────────────────────────────────┘
         ↓ al termine della sessione
┌─────────────────────────────────────────────┐
│  EPISODIC MEMORY (ChromaDB)                  │
│  Cosa è successo, quando, con quale esito    │
│  "Ieri Roby ha chiesto di X, ho risposto Y"  │
│  Append-only, score decay nel tempo          │
│  Recupero per similarità semantica           │
└─────────────────────────────────────────────┘
         ↓ fatti stabili estratti
┌─────────────────────────────────────────────┐
│  SEMANTIC MEMORY (ChromaDB)                  │
│  Fatti su Roby e sul suo mondo               │
│  "Roby usa Mac M1 Max", "progetto X è Y"    │
│  Aggiornabile, non append-only               │
│  Source: conversazioni + documenti           │
└─────────────────────────────────────────────┘
         ↓ documenti indicizzati
┌─────────────────────────────────────────────┐
│  KNOWLEDGE BASE (Obsidian vault)             │
│  Documenti che Roby dà da studiare           │
│  Chunked e indicizzati in ChromaDB           │
│  Athena legge E scrive note nel vault        │
│  Link [[wikilink]] per navigazione grafo     │
└─────────────────────────────────────────────┘
```

---

## Come funziona il recupero

Ogni volta che Athena riceve un input:

```
input utente
    ↓
1. Cerca in Working Memory (contesto corrente)
2. Cerca in Semantic Memory (fatti su Roby)
3. Cerca in Episodic Memory (sessioni passate rilevanti)
4. Cerca in Knowledge Base (documenti indicizzati)
    ↓
Assembla contesto → invia a LLM con prompt costruito
    ↓
Risposta → estrattore fatti → aggiorna Semantic Memory se serve
```

---

## Memory extraction post-sessione

Al termine di ogni conversazione, Athena esegue:

```python
# Pseudo-codice
facts = extract_facts(conversation)
# Es: "Roby vuole che X", "Roby preferisce Y", "Il progetto Z ha problema W"

for fact in facts:
    if is_new(fact):
        semantic_memory.add(fact)
    elif conflicts(fact, existing):
        semantic_memory.update(fact)  # non cancella, versiona

episodic_memory.add(session_summary)
```

---

## Struttura vault — due livelli separati

### Google Drive — AthenaInput/ (input controllato da Roby)
Cartella dedicata nel vault Google Drive di Roby.
Athena monitora SOLO questa cartella, niente altro del vault.
Roby ci mette file da qualsiasi device (Mac, iPhone via app GDrive).
L'atto di mettere un file qui = consenso esplicito a far studiare Athena.

```
Google Drive/
└── AthenaInput/
    ├── documento_progetto.pdf
    ├── note_architettura.md
    └── [qualsiasi file Roby vuole che Athena sappia]
```

### Locale — /vault/athena/ (memoria privata, solo Mac)
Athena legge e scrive qui. Non sincronizzato su cloud. Privacy totale.

```
/vault/athena/
├── knowledge/        ← copie locali dei file da AthenaInput (elaborati)
│   └── [file + metadata: data elaborazione, chunks, fonte]
└── notes/            ← note che Athena scrive a se stessa
    ├── sessioni/     ← sommari sessioni per mese
    └── self/         ← osservazioni su se stessa, changelog
```

### Flusso elaborazione documento

```
Roby mette file in AthenaInput/ (da Mac o iPhone)
        ↓
watchdog rileva nuovo file (entro 30s)
        ↓
Athena elabora: chunking → embedding → ChromaDB
        ↓
Copia file in /vault/athena/knowledge/ (locale)
        ↓
Notifica Roby: "Ho studiato [nome file] — X chunk indicizzati"
        ↓
File originale rimane su Google Drive intatto
```

### Note
- Athena funziona offline con le copie locali
- Se un file viene modificato in AthenaInput/ → Athena re-indicizza automaticamente
- Se un file viene rimosso da AthenaInput/ → Athena mantiene la copia locale (non dimentica)

---

## Principio append-only

Dalla vecchia Athena: **non si cancella, si aggiunge con score**.

I ricordi non vengono cancellati. Se un fatto diventa obsoleto:
- Il vecchio ricordo riceve score negativo (decade nel recupero)
- Il nuovo fatto viene aggiunto con score pieno
- In caso di conflitto esplicito: Athena nota la contraddizione

Questo preserva la storia e permette di "tornare indietro" se serve.

---

## Embedding

- **Modello:** `nomic-embed-text` via Ollama (locale, leggero)
- **Chunking:** paragrafi semantici, max 512 token, overlap 50 token
- **Per documenti Obsidian:** heading-aware (il path heading viene incluso nel chunk per contesto)

Esempio chunk con heading path:
```
[Progetto Misterlab > Architettura > Database]
Il database usa Supabase PostgreSQL con RLS abilitato su tutte le tabelle...
```

---

## roby.md — profilo utente

File speciale, sempre iniettato nel system prompt.
Contiene le informazioni stabili su Roby: preferenze, macchine, progetti attivi, stile comunicativo.
Athena lo aggiorna autonomamente quando impara qualcosa di nuovo (con diff mostrato a Roby).

**Fonte:** athenaOld/roby.md — da copiare e aggiornare.
