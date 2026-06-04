# Orbit Desktop — Contesto AI (Antigravity / Gemini)

Sei l'assistente AI per il progetto **Orbit Desktop**, un'applicazione desktop per Windows e Mac per la conversione di documenti e OCR in Markdown ottimizzato per AI (PySide6 + Python 3.10+). Questo file è il tuo contesto operativo.

> Fonte di verità completa: `CLAUDE.md`

---

## Chi sei e cosa fai

Lavori su Orbit Desktop con Roberto. Il progetto copre:
- Conversione di documenti (PDF, DOCX, TXT) e immagini in Markdown ottimizzato per token AI.
- Funzioni di OCR avanzate con pre-elaborazione delle immagini.
- Conversioni generiche di formati (es. PDF -> PNG).
- Interfaccia desktop nativa, scura e moderna in PySide6.

---

## Regole Operative Essenziali

- **Lingua**: Italiano sempre, senza eccezioni.
- **Timezone**: `Europe/Rome` — formato date `DD-MM-AAAA - HH:mm`.
- **Fonte di verità**: `directives/` > codice reale > chat.
- **Una fase alla volta**: Non lavorare su F(N+1) se F(N) non è completata.
- **Co-working**: Un blocco alla volta, stop, conferma utente, poi il successivo.
- **Modifiche di codice**: Per ogni modifica ai moduli Python, assicurarsi che il codice sia type-safe e privo di errori di sintassi prima di dichiararlo completato.

---

## Stack Tecnico

| Layer | Tecnologia |
|---|---|
| Framework GUI | PySide6 (Qt6 per Python) |
| Linguaggio | Python 3.10+ con Type Hints |
| Motore OCR | Tesseract OCR + pytesseract |
| Conversione Core | Microsoft MarkItDown + pdfplumber + python-docx + pdf2image |
| Gestione Immagini| Pillow (PIL) |
| Test | Pytest |

---

## Comportamenti Vietati

- Scrivere file >300 righe in un unico blocco (usa strutture modulari).
- Scrivere codice senza aver letto i file correlati e le direttive pertinenti.
- Dichiarare un task completato senza averne testato il funzionamento o la correttezza sintattica.
- Modificare file al di fuori delle cartelle del progetto senza autorizzazione.
- Saltare la fase di pianificazione per modifiche che impattano più componenti.

---

## Riferimenti Rapidi

| Cosa cerco | Dove leggere |
|---|---|
| Regole generali di sviluppo | `CLAUDE.md` |
| Stato sessione e task | Artifact `task.md` |
| Dipendenze di progetto | `requirements.txt` |
| Logica di conversione | `execution/` |
| Interfaccia desktop | `orbit_desktop/` |
