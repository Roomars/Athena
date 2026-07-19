# Ari — Knowledge Base, Orbit e Local NotebookLM

## Tre sistemi che si connettono

```
ORBIT (software separato)
  Converte qualsiasi documento → Markdown ottimizzato per AI
        ↓
ATHENA INPUT (Google Drive/AthenaInput/)
  Roby deposita i file da far studiare ad Ari
        ↓
ARI KNOWLEDGE ENGINE (locale)
  Indicizza, chunka, embeda, risponde a domande
  → Local NotebookLM equivalent
```

---

## Orbit — Pipeline Books to Markdown

Orbit è un software separato (già in sviluppo) che Ari NON controlla.
Il suo output alimenta il vault di Ari.

### Cosa fa Orbit
Converte qualsiasi sorgente in Markdown ottimizzato per LLM:

| Input | Metodo | Note |
|---|---|---|
| PDF digitale (testo) | pdfminer / pymupdf | Estrazione diretta |
| PDF scansionato | Tesseract OCR + post-processing | Richiede qualità scan decente |
| EPUB / ebook | ebooklib | Struttura capitoli preservata |
| DOCX / Word | python-docx | Headers → Markdown headers |
| Immagine (foto libro) | OCR + deskew | Preprocessing qualità |
| Web page | trafilatura / readability | Solo contenuto, no sidebar |
| Testo grezzo | cleaning + formatting | Normalizzazione |

### Output Orbit
Markdown con frontmatter YAML:
```markdown
---
title: "Il Titolo del Libro"
author: "Nome Autore"
source: "pdf_digitale"
date_processed: "2026-06-14"
pages: 342
language: "it"
tags: ["architettura", "software", "patterns"]
---

# Capitolo 1 — Il Titolo

Il contenuto del capitolo in Markdown pulito...

## 1.1 Sottosezione

...
```

### Perché Markdown ottimizzato per AI
I LLM leggono Markdown meglio di testo grezzo:
- Headers (`#`, `##`) danno struttura semantica
- Il path heading viene incluso nei chunk: `[Cap 1 > 1.1 > paragrafo]`
- Nessun carattere spazzatura da OCR (normalizzati da Orbit)
- Token count ridotto: stesso contenuto, meno token sprecati su formatting

---

## AthenaInput — il confine Orbit → Ari

```
Orbit produce file.md
  ↓
Roby sposta in Google Drive/AthenaInput/
  ↓ (oppure deposita direttamente da iPhone)
watchdog di Ari rileva nuovo file
  ↓
Ari processa: chunking → embedding → ChromaDB + copia locale
  ↓
Notifica: "Ho studiato [file] — X chunk indicizzati"
```

### Struttura AthenaInput consigliata
```
Google Drive/AthenaInput/
├── libri/
│   ├── clean_code.md
│   └── pragmatic_programmer.md
├── articoli/
│   └── swiftui_animations_2026.md
├── progetti/
│   └── misterlab_spec.md
└── note/
    └── idee_architettura.md
```

---

## Local NotebookLM — capacità equivalenti

Ari offre le stesse capacità di NotebookLM ma in locale, zero cloud.

### Cosa fa NotebookLM (Google)
1. Carica documenti → crea un "notebook"
2. Fai domande sui documenti → risponde con citazioni
3. Genera sommari automatici
4. Genera FAQ
5. Genera "audio overview" (due voci che discutono del contenuto)
6. Identifica connessioni tra documenti diversi

### Equivalente Ari (locale, privacy totale)

**1. Notebook per progetto / topic**
```
"Ari, crea un notebook su Clean Code"
→ Indica quali documenti includere (o seleziona tag/cartella)
→ Ari crea contesto isolato per quel corpus
→ Puoi fare domande specifiche solo su quei documenti
```

**2. Q&A con citazioni**
```
"Ari, nel libro Clean Code cosa dice riguardo ai nomi delle variabili?"
→ Ari recupera i chunk rilevanti
→ Risponde con citazione del testo originale e numero di sezione
→ "A pagina 18, sezione 2.3: '...'"
```

**3. Sommario automatico**
```
"Ari, fammi un sommario di clean_code.md"
→ Sommario strutturato con i punti principali
→ Livello di dettaglio configurabile (executive / medio / approfondito)
```

**4. FAQ generata**
```
"Ari, genera 10 domande frequenti su questo libro"
→ Lista Q&A estratta dai contenuti
→ Utile per studiare o creare documentazione
```

**5. Briefing audio**
```
"Ari, leggi un riassunto di questo documento"
→ TTS (Federica Premium) legge il sommario
→ Modalità "podcast": Ari recita il contenuto in formato narrativo
```

**6. Connessioni tra documenti**
```
"Ari, cosa hanno in comune Clean Code e Pragmatic Programmer?"
→ Ari ricerca in entrambi i corpus
→ Identifica temi ricorrenti, contraddizioni, complementarità
```

**7. Estrazione strutturata**
```
"Ari, estrai tutte le date e scadenze da questo documento"
"Ari, elenca tutti i pattern di design menzionati"
"Ari, trova tutte le citazioni di autori terzi"
```

---

## Gestione notebook (UI)

Accessibile in Chat mode → tab "Notebook":

```
NOTEBOOK
├── [Tutti i documenti]
├── Clean Code (2 docs, 847 chunks)
├── Architettura Software (5 docs, 2341 chunks)
├── Misterlab (3 docs, 412 chunks)
└── [+ Nuovo Notebook]
```

Per ogni notebook:
- Documenti inclusi (con data indicizzazione)
- Dimensione (chunk count, token totali)
- Query recenti
- Pulsanti: Sommario / FAQ / Aggiungi doc / Elimina

---

## Skill `knowledge_ops`

Skill dedicata alla gestione del knowledge base:

```python
SKILL_META = {
    "name": "knowledge_ops",
    "triggers": ["studia", "leggi", "notebook", "sommario", "faq", 
                 "cosa dice", "nel documento", "nel libro"],
}

async def execute(params):
    action = params["action"]
    # create_notebook, query_notebook, summarize,
    # generate_faq, find_connections, extract_structured
```

---

## Re-indicizzazione e manutenzione

- **Modifica documento:** watchdog rileva → re-index automatico solo dei chunk modificati
- **Eliminazione:** rimuove chunk dal ChromaDB, mantiene copia locale (archivio)
- **Re-index completo:** "Ari, re-indicizza tutto" → utile dopo cambio modello embedding
- **Stats:** "Ari, quanti documenti hai studiato?" → count docs/chunks/token
