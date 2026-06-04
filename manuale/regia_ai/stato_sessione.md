# Stato Sessione — Athena

**Ultimo aggiornamento:** 04-06-2026 - 23:00

---

## Fase attiva

**FASE 1** — Fix & UI base

---

## Stato corrente

Athena v0.3 — build DMG funzionante, Brain RAG attivo, UI ridisegnata Claude-style.
App non ancora testabile perché blockers attivi (vedi sotto).

---

## Lavoro completato in questa sessione

**Infrastruttura:**
- Repo GitHub creato: `Roomars/Athena` — tutto pushato
- `.gitignore` con exclusioni corrette (brain/, backups/, target/, *.db)
- `CLAUDE.md` riscritto per Athena (da Orbit Desktop)
- `settings.json` aggiornato con permessi corretti
- `manuale/` struttura completa creata

**Agenti Claude Code:**
- Specialist sostituiti: OCR+PySide6 → `tauri-specialist` + `ui-web-specialist`
- Tutti gli agenti allineati ad Athena

**Brain RAG:**
- `nomic-embed-text` installato in Ollama
- `core/brain.py` — ChromaDB, embedding vault Obsidian
- `core/watcher.py` — file watcher auto-embed
- `core/app.py` — RAG su ogni messaggio
- Vault path: `~/Library/CloudStorage/GoogleDrive-.../AI_Brain`
- Test: 37 chunk indicizzati, ricerca Coach/U17 funzionante

**UI Claude-style:**
- `index.html` ridisegnato: sidebar beige, no bolla Athena, max-width 680px, Markdown via marked.js, dot animati, barra contesto
- Riferimento UI Claude Desktop salvato in `manuale/gui/`
- Riferimento native Mac salvato in `manuale/gui/`

**Tauri / App:**
- `titleBarStyle: "Overlay"` — traffic lights su HTML
- Drag region sulla sidebar, padding 28px per traffic lights
- Menu nativo macOS: Athena / Conversazione / Modifica con ⌘N ⌘W ⌘Q
- Binario rinominato `Athena` (maiuscolo) come Claude Desktop
- Target DMG aggiunto — genera `Athena_0.1.0_aarch64.dmg`
- `ActivationPolicy::Regular` — app visibile nel Dock
- Menu tray: solo Athena OS / Apri / Nuova conversazione / Esci
- Fix icona app: usa `athena-app.png` vera invece del placeholder Pillow
- Fix tray icon: usa `src-tauri/icons/tray-icon.png` invece del placeholder 1KB
- Fix backend crash: `Observer | None` → `Optional[Observer]` (Python 3.9)

---

## Blocker attivi

### BLK-1 — "Internal Server Error" all'avvio dell'app
**Sintomo**: finestra nera con "Internal Server Error"
**Causa probabile**: il backend crasha a runtime, probabilmente per errore in `core/brain.py` o `core/app.py` durante il lifespan startup. Il Brain tenta di indicizzare il vault e potrebbe fallire con un'eccezione non gestita che porta FastAPI a rispondere 500.
**Da fare**: aggiungere try/except robusto nel lifespan, testare avvio backend isolato dal terminale con `./start.sh`, leggere i log di uvicorn.

### BLK-2 — Titolo finestra mostra "Tauri App"
**Sintomo**: la titlebar mostra "Tauri App" invece di "Athena"
**Causa**: l'utente ha probabilmente la vecchia versione dell'app ancora installata in `/Applications/`. Il nuovo `.app` non è stato sostituito.
**Da fare**: `pkill -f Athena`, rimuovere `/Applications/Athena.app`, reinstallare dal nuovo DMG, eseguire `xattr -cr /Applications/Athena.app`.

---

## Prossime priorità

1. **Risolvere BLK-1** — debug backend crash, rendere il lifespan fault-tolerant
2. **Risolvere BLK-2** — reinstallazione pulita dell'app
3. **Backend bundled** — bundle core/+static/ dentro `.app`, setup venv automatico al primo avvio
4. Markdown rendering nelle risposte (già in UI, da verificare funzionante)
5. Quick Entry ⌘⇧A

---

## Changelog

| Data | Cosa |
|---|---|
| 04-06-2026 | Setup repo GitHub, agenti, CLAUDE.md, manuale/ |
| 04-06-2026 | Brain RAG: ChromaDB + watcher vault Obsidian (37 chunk) |
| 04-06-2026 | UI Claude-style: ridisegno completo index.html |
| 04-06-2026 | Tauri: menu nativo, DMG, Dock, fix icone, fix Python 3.9 |
