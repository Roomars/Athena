# Orbit Desktop — Contesto AI

Questo file viene caricato automaticamente ad ogni sessione e definisce le regole operative critiche per lo sviluppo di **Orbit Desktop**.

---

## Descrizione Progetto

Orbit Desktop è un'applicazione desktop personale cross-platform (Windows & Mac) scritta in **Python & PySide6 (Qt6)**. È uno strumento a uso personale con due anime:

1. **AI Studio** (priorità) — converte documenti (PDF, DOCX, TXT) e immagini (OCR) in Markdown ottimizzato per token LLM
2. **PDF Tools** — coltellino svizzero per la gestione PDF (unisci, dividi, riordina, ruota, converti)

L'architettura è **modulare**: Orbit è un contenitore che ospita moduli indipendenti. Ogni modulo ha logica, flussi e UI propri. Aggiungere un modulo non tocca il codice degli altri.

---

## Regole Operative Bloccate

- **Lingua**: Italiano sempre, sia nelle risposte che nella documentazione di progetto
- **Timezone**: `Europe/Rome` — formato data/ora: `DD-MM-AAAA - HH:mm`
- **Fonte di verità**: `manuale/` > codice reale > chat
- **Co-working**: Un blocco alla volta. Stop, conferma utente, poi il blocco successivo
- **Ambito**: Rispettare rigorosamente il focus sulle funzioni desktop di Orbit
- **Code guard**: Invocare `/orbit-code-guard` dopo ogni modifica `.py` prima di dichiarare il task completato

---

## Architettura a 3 Livelli

1. **`directives/`** — Procedure operative standard (SOP) per i flussi di conversione
2. **`orbit_desktop/`** — GUI PySide6, navigazione modulare, thread worker
3. **`execution/`** — Motore deterministico: conversioni, OCR, esportazione. Nessuna logica GUI

---

## Struttura Moduli

```
orbit_desktop/
└── modules/
    ├── ai_studio/      ← priorità — conversione documenti e OCR
    └── pdf_tools/      ← strumenti PDF pratici
```

Un modulo non importa mai da un altro modulo.
La logica pesante risiede sempre in `execution/`, mai nei moduli.

---

## Linee Guida per il Codice Python

- **Type Safety**: Type hints sempre — evitare `Any` non motivato
- **Threading**: Nessuna operazione bloccante nel thread UI — sempre `QThread` / `QRunnable`
- **Gestione Errori**: Eccezioni catturate in `execution/`, propagate come messaggi leggibili alla GUI
- **Moduli**: Nessun file > 300 righe — spezzare prima di continuare
- **Stile UI**: Design scuro, premium, moderno — valori di stile in QSS, non hardcodati in Python

---

## Ufficio AI — Struttura

### Comandi di sessione
| Comando | Quando |
|---|---|
| `/Apri Sessione` | Inizio sessione — sync GitHub, health check, stato progetto |
| `/Salva Sessione` | Durante la sessione — salva stato e pusha su GitHub |
| `/Chiudi Sessione` | Fine sessione — checklist completa e push finale |

### Skill operative
| Skill | Quando |
|---|---|
| `/orbit-code-guard` | Obbligatorio dopo ogni modifica `.py` |
| `/orbit-skill-improver` | Quando si aggiungono nuovi ERR-* a `errori_appresi.md` |

### Team di agenti (`.claude/agents/`)
**Core Team** — universale:
- `core/architetto` (Opus) — decisioni strutturali, DEC-*
- `core/senior-dev` (Sonnet) — implementazione Python/Qt
- `core/qa-engineer` (Sonnet) — test e validazione
- `core/tech-writer` (Haiku) — manuale e documentazione
- `core/build-engineer` (Haiku) — packaging e dipendenze

**Specialist Orbit** — dominio specifico:
- `specialist/ocr-specialist` (Sonnet) — pipeline OCR e imaging
- `specialist/ux-desktop-engineer` (Sonnet) — GUI e UX

### Fonte di verità del progetto (`manuale/`)
| Cartella | Contenuto |
|---|---|
| `manuale/regia_ai/` | Stato sessione, checkpoint, errori appresi, session log |
| `manuale/moduli/` | Documentazione di ogni modulo del prodotto |
| `manuale/flussi/` | Un file `.md` per ogni flusso di esecuzione |
| `manuale/architettura/` | Decisioni strutturali, threading, dipendenze |
| `manuale/gui/` | Componenti UI, navigazione, design system |
| `manuale/roadmap/` | Backlog e decisioni architetturali (DEC-*) |

---

## Setup di Sviluppo

### Dipendenze di Sistema
1. **Tesseract OCR** — Windows: installer UB Mannheim + PATH / macOS: `brew install tesseract tesseract-lang`
2. **Poppler** — Windows: binari + PATH / macOS: `brew install poppler`

### Ambiente Python
```bash
# Crea venv
python -m venv .venv

# Attiva — Windows:
.venv\Scripts\activate
# Attiva — macOS:
source .venv/bin/activate

# Installa
pip install -r requirements.txt

# Avvio sviluppo
python -m orbit_desktop.main
```

---

## Workflow Multi-macchina (Windows + macOS)

Tutte le repository sono su GitHub. Il flusso garantisce continuità tra le due macchine:

1. **Inizio sessione** → `/Apri Sessione` scarica l'ultimo stato da GitHub
2. **Durante la sessione** → `/Salva Sessione` salva e pusha in qualsiasi momento
3. **Fine sessione** → `/Chiudi Sessione` push finale — la prossima macchina troverà tutto aggiornato
