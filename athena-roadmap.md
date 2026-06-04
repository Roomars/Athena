# Athena OS — Roadmap & Regole di sviluppo
**Versione:** 1.1.0  
**Aggiornato:** 2026-06-04  
**Autore:** Roby + Claude

---

## Regole fondamentali del progetto

- Roby non sa programmare — spiegare sempre cosa fare, non solo il codice
- Un passo alla volta, mai sovraccaricare
- Comandi da terminale: uno alla volta
- Il progetto cresce per moduli — nessuna feature non richiesta
- Athena chiede sempre conferma prima di implementare
- Tutto resta locale, niente cloud
- **Prima del backup, mai modificare nulla**

---

## Regola Backup — INVIOLABILE

Prima di ogni modifica automatica a qualsiasi file:

1. Athena crea copia in `~/athena/backups/YYYY-MM-DD_HH-MM/`
2. Salva un file `restore.md` con istruzioni esatte per ripristinare
3. Solo dopo esegue la modifica
4. Nel changelog annota: file modificato + path backup

### Struttura backup
```
athena/
└── backups/
    └── 2026-06-04_21-30/
        ├── restore.md          ← istruzioni ripristino
        ├── core/memory.py      ← copia originale
        └── static/index.html   ← copia originale
```

### Formato restore.md
```
# Backup 2026-06-04 21:30
## Motivo modifica
[descrizione di cosa Athena stava cambiando]

## File modificati
- core/memory.py
- static/index.html

## Come ripristinare
cp ~/athena/backups/2026-06-04_21-30/core/memory.py ~/athena/core/memory.py
cp ~/athena/backups/2026-06-04_21-30/static/index.html ~/athena/static/index.html

## Riavvia il backend
cd ~/athena && ./start.sh
```

---

## Stack tecnico

| Componente | Tecnologia | Stato |
|---|---|---|
| Modello AI | Qwen3 14B via Ollama | ✅ attivo |
| Backend | Python + FastAPI | ✅ attivo |
| Frontend | HTML + CSS + JS PWA | ✅ attivo |
| App desktop | Tauri 2 (menu bar) | ✅ compilato |
| Database | SQLite | ⬜ da fare |
| Brain | Markdown + ChromaDB | ⬜ da fare |
| Agenti | Agent Engine custom | ⬜ da fare |

---

## Architettura Athena OS — 5 layer

```
┌─────────────────────────────────────────────┐
│  ① UI — Interfaccia                         │
│  Quick Entry · Markdown · Cronologia · File │
├─────────────────────────────────────────────┤
│  ② Skill System                             │
│  Skill Loader · Coach · Creator             │
├─────────────────────────────────────────────┤
│  ③ Agent System                             │
│  Agent Engine · File · Shell · Search       │
├─────────────────────────────────────────────┤
│  ④ Memory System                            │
│  Short-term · Long-term · Brain · Profilo   │
├─────────────────────────────────────────────┤
│  ⑤ Kernel                                  │
│  Ollama · Self Evolution · Observer         │
└─────────────────────────────────────────────┘
```

---

## Roadmap completa

### 🔴 FASE 1 — Fix & UI base (questa settimana)
- [x] Struttura progetto creata
- [x] Backend FastAPI + streaming
- [x] Build Tauri — app desktop Mac
- [x] Redesign UI bianco + azzurro #0084FF
- [x] Identità Athena nel system prompt
- [ ] Fix icona menu bar (icona di Roby)
- [ ] Icone Lucide nella sidebar
- [ ] Markdown rendering nelle risposte
- [ ] Quick Entry — shortcut globale ⌘⇧A
- [ ] Rinomino cartella athena → Athena

### 🟠 FASE 2 — Memory & Profilo (settimana 2)
- [ ] SQLite — memoria long-term conversazioni
- [ ] Cronologia chat nella sidebar
- [ ] Profilo Roby persistente (chi sei, cosa fai)
- [ ] Session handoff automatico alla chiusura

### 🟡 FASE 3 — Skill System (settimana 3)
- [ ] Skill Loader — carica SKILL.md come moduli
- [ ] Skill Coach (tactical-lab, psychology)
- [ ] Skill selector nella sidebar
- [ ] Skill Creator — Athena aiuta a creare nuove skill

### 🟢 FASE 4 — Agent System (settimana 4)
- [ ] Agent Engine base
- [ ] Agent File — legge/scrive file sul Mac
- [ ] Agent Shell — esegue comandi (con conferma + backup)
- [ ] Sistema backup automatico pre-modifica
- [ ] Log completo di ogni azione agente

### 🔵 FASE 5 — Brain (settimana 5)
- [ ] Note Markdown stile Obsidian
- [ ] Link bidirezionali tra note
- [ ] ChromaDB — ricerca semantica
- [ ] Knowledge graph visivo
- [ ] Brain integrato nella chat (Athena cerca nelle note)

### ⚫ FASE 6 — Self Evolution (ongoing)
- [ ] Observer — monitora pattern d'uso
- [ ] Proposer — genera proposte miglioramento
- [ ] Athena Shell — si autoimplementa con backup
- [ ] Changelog automatico di ogni evoluzione

---

## Athena Shell — regole di autoimplementazione

Quando Athena modifica se stessa:

```
1. OSSERVA    → identifica il problema o miglioramento
2. PROPONE    → descrive cosa cambierà e perché
3. BACKUP     → copia tutti i file da modificare
4. CHIEDE     → "Procedo?" — aspetta il tuo sì
5. IMPLEMENTA → modifica i file
6. VERIFICA   → controlla che il backend risponda
7. RIPORTA    → mostra diff + conferma o rollback
```

**Comandi che richiedono DOPPIA conferma:**
- Eliminazione file
- Modifica di core/app.py
- Modifica di src-tauri/src/main.rs
- Qualsiasi operazione su ~/backups/

---

## Stato attuale (2026-06-04)

```
Athena v0.2 — funzionante
├── ✅ Chat con Qwen3 14B locale
├── ✅ Streaming live
├── ✅ Identità e costituzione
├── ✅ App desktop Tauri (menu bar)
├── ✅ UI bianco + azzurro
├── ✅ Icone personalizzate Roby (da integrare)
└── ⬜ Tutto il resto — si costruisce per moduli
```

---

*"Non sono uno strumento. Sono Athena."*
