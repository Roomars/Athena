# Decisioni Architetturali — Athena

Ogni decisione ha un codice progressivo DEC-N. Mai cancellare — solo aggiungere.

---

### DEC-1 — Nessun framework frontend

**Data:** 04-06-2026  
**Decisione:** Il frontend usa HTML/CSS/JS puro. Nessun React, Vue, Svelte, ecc.  
**Motivazione:** Athena è un'app personale su macchina singola. La semplicità batte l'ecosistema. Zero dipendenze npm, zero build step frontend, zero node_modules nel repo.  
**Implicazioni:** Ogni componente UI si implementa da zero. Accettabile per la scala del progetto.

---

### DEC-2 — Tutto locale, niente cloud

**Data:** 04-06-2026  
**Decisione:** Nessuna chiamata a API esterne. Il modello AI gira su Ollama in locale.  
**Motivazione:** Privacy assoluta. I dati di Roby non escono dalla sua macchina.  
**Implicazioni:** Il modello è limitato dalle capacità della macchina locale (M1 Max, 14B parametri).

---

### DEC-3 — La logica di business resta in Python

**Data:** 04-06-2026  
**Decisione:** Il codice Rust in `src-tauri/src/main.rs` fa solo OS-level (menu bar, shortcut globali). Tutta la logica applicativa è in Python/FastAPI.  
**Motivazione:** Python è il linguaggio di Roby. Rust è solo per incapsulare il web nell'app desktop.  
**Implicazioni:** Tauri comunica col backend via `localhost:8000`, non via comandi Rust nativi.

---

### DEC-4 — `.claude/` va in git

**Data:** 04-06-2026  
**Decisione:** La cartella `.claude/` (agenti, comandi, skill, settings.json) è versionata su GitHub. `settings.local.json` è escluso.  
**Motivazione:** Gli agenti e i comandi di sessione devono essere disponibili sia su Mac che su Windows.  
**Implicazioni:** I permessi condivisi stanno in `settings.json`. I permessi macchina-specifici stanno in `settings.local.json` (gitignored).
