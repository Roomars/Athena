# Backlog — Athena

**Aggiornato:** 04-06-2026

---

## FASE 1 — Fix & UI base

| Task | Stato | Note |
|---|---|---|
| Struttura progetto creata | ✅ | |
| Backend FastAPI + streaming | ✅ | |
| Build Tauri — app desktop Mac | ✅ | |
| Redesign UI bianco + azzurro #0084FF | ✅ | |
| Identità Athena nel system prompt | ✅ | |
| Fix icona menu bar | ⬜ | Usare icona personalizzata di Roby (`static/icons/athena-menubar.png`) |
| Icone Lucide nella sidebar | ⬜ | Sostituire emoji con SVG Lucide |
| Markdown rendering nelle risposte | ⬜ | `**grassetto**`, `# titoli`, `` `code` ``, liste |
| Quick Entry — shortcut globale ⌘⇧A | ⬜ | Overlay + Tauri global shortcut |
| Rinomino cartella athena → Athena | ⬜ | Bassa priorità |

---

## FASE 2 — Memory & Profilo

| Task | Stato | Note |
|---|---|---|
| SQLite — memoria long-term | ⬜ | `core/database.py`, file `athena.db` (gitignored) |
| Cronologia chat nella sidebar | ⬜ | Lista sessioni passate cliccabili |
| Profilo Roby persistente | ⬜ | Chi sei, cosa fai — incluso nel system prompt |
| Session handoff automatico | ⬜ | All'avvio carica contesto ultima sessione |

---

## FASE 3 — Skill System

| Task | Stato | Note |
|---|---|---|
| Skill Loader — carica SKILL.md | ⬜ | File in `modules/skills/` |
| Skill Coach | ⬜ | tactical-lab, psychology |
| Skill selector nella sidebar | ⬜ | |
| Skill Creator | ⬜ | Athena aiuta a creare skill |

---

## FASE 4 — Agent System

| Task | Stato | Note |
|---|---|---|
| Agent Engine base | ⬜ | Orchestratore task-oriented |
| Agent File | ⬜ | Legge/scrive file con backup obbligatorio |
| Agent Shell | ⬜ | Esegue comandi con doppia conferma |
| Sistema backup automatico pre-modifica | ⬜ | `backups/YYYY-MM-DD_HH-MM/` |
| Log completo azioni agente | ⬜ | |

---

## FASE 5 — Brain

| Task | Stato | Note |
|---|---|---|
| Note Markdown stile Obsidian | ⬜ | In `brain/notes/` (gitignored) |
| Link bidirezionali tra note | ⬜ | |
| ChromaDB — ricerca semantica | ⬜ | Embedding con nomic-embed-text via Ollama |
| Knowledge graph visivo | ⬜ | In valutazione |
| Brain integrato nella chat | ⬜ | RAG locale — Athena cerca nelle note |

---

## FASE 6 — Self Evolution (ongoing)

| Task | Stato | Note |
|---|---|---|
| Observer — monitora pattern d'uso | ⬜ | |
| Proposer — genera proposte miglioramento | ⬜ | |
| Athena Shell — autoimplementazione | ⬜ | Vedi flussi/self-evolution.md |
| Changelog automatico evoluzioni | ⬜ | |
