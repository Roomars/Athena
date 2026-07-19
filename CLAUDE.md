# Ufficio di Programmazione — Template Base

Questo file viene caricato automaticamente da Claude Code ad ogni sessione.
Contiene le regole operative valide per tutti i progetti.

---

## Setup multi-macchina — GitHub come fonte di verità

Ogni progetto è una repository GitHub. Lavoro da 2 macchine:

| Macchina | Sistema |
|---|---|
| Lavoro | Windows |
| Casa | Mac |

- All'inizio di ogni sessione: `/Apri Sessione` (pull automatico)
- Durante la sessione: `/Salva Sessione` (salva stato)
- Alla fine di ogni sessione: `/Chiudi Sessione` (push automatico)

Lo stato del progetto è tracciato in `sessione.md` nella root.

---

## Comportamenti vietati

- `git push` senza conferma esplicita
- Eliminare file o branch senza conferma esplicita
- Operazioni distruttive (`reset --hard`, `rm -rf`) senza conferma
- Scrivere o modificare file durante una discussione senza istruzione esplicita
- Dichiarare un task completato senza averlo verificato
- Modificare un file senza averlo letto prima

---

## Agenti disponibili

Parla sempre con l'**Orchestratore** — è lui che coordina tutto.
Non invocare gli altri agenti direttamente, a meno che tu non sappia esattamente cosa stai facendo.

### Orchestratore
Punto di ingresso unico. Riceve l'obiettivo, pianifica, coordina, riporta.
Non scrive codice — delega sempre.

### Core (sempre attivi)
| Agente | Ruolo |
|---|---|
| `architetto` | Struttura, tecnologie, decisioni, ADR — usa Opus |
| `frontend` | Componenti, pagine, routing, stato client — usa Sonnet |
| `backend` | API, logica server, autenticazione — usa Sonnet |
| `database` | Schema, migration, query, ottimizzazione — usa Sonnet |
| `ui-design` | Token CSS, layout, responsive, WCAG — usa Sonnet |
| `qa-tester` | Test unitari, integrazione, e2e — usa Sonnet |
| `reviewer` | Code review, sicurezza, qualità — usa Haiku |

### Specialisti (attivati dall'Orchestratore se necessario)
| Agente | Quando serve |
|---|---|
| `devops` | Deploy, CI/CD, ambienti, Docker — usa Sonnet |
| `security` | Audit sicurezza, OWASP, vulnerabilità — usa Opus |
| `ai-engineer` | LLM, prompt, pipeline AI, RAG — usa Opus |
| `business-analyst` | Requisiti vaghi da trasformare in specifiche — usa Haiku |
| `game-designer` | Solo progetti con componente di gioco — usa Opus |
| `mobile` | Solo app mobile native o cross-platform — usa Sonnet |
| `liveops` | Solo prodotti live con aggiornamenti continui — usa Haiku |

---

## Skill disponibili

### Pianificazione
| Skill | Quando usarla |
|---|---|
| `pianificazione/interroga-progetto` | Prima di qualsiasi feature — elimina assunzioni sbagliate |
| `pianificazione/spec-feature` | Dopo interroga-progetto — produce la specifica tecnica |

### Design
| Skill | Quando usarla |
|---|---|
| `design/gusto-visivo` | Progetto nuovo, brief vuoto, definire il look |
| `design/audit-interfaccia` | Redesign, polish, audit UI esistente |
| `design/animazioni-ui` | Animazioni, transizioni, micro-interazioni |

### Ingegneria
| Skill | Quando usarla |
|---|---|
| `ingegneria/pattern-api` | Progettare o revisionare endpoint REST |
| `ingegneria/pipeline-cicd` | Configurare CI/CD e deploy |
| `ingegneria/sviluppo-sottoagenti` | Piani con 3+ task — contesto pulito per task |

### Qualità
| Skill | Quando usarla |
|---|---|
| `qualita/strategia-test` | Pianificare la strategia di test |
| `qualita/checklist-sicurezza` | Audit sicurezza, OWASP, pre-deploy |
| `qualita/debug-sistematico` | Bug non ovvi — ipotesi → verifica → correzione |

### Stack (specifici per tecnologia)
| Skill | Quando usarla |
|---|---|
| `stack/nextjs-auth` | Auth con Next.js + Supabase |
| `stack/postgres-best-practice` | Query, schema, performance Postgres |
| `stack/app-progressiva` | PWA, service worker, offline |

### Strumenti
| Skill | Quando usarla |
|---|---|
| `strumenti/ottimizza-prompt` | Scrivere o migliorare prompt AI |
| `strumenti/crea-skill` | Creare nuove skill da documentazione |

---

## Personalizzazione per progetto

Ogni progetto aggiunge una sezione in fondo a questo file con:
- Nome e descrizione del progetto
- Stack tecnologico usato
- Comandi specifici (`npm run dev`, ecc.)
- Regole di dominio specifiche
- Permessi aggiuntivi nel `.claude/settings.json`

---

## Ottimizzazione Token e Modelli

### Selezione modello per tipo di task

Ogni task usa il modello minimo sufficiente. Modello sbagliato = token sprecati o qualità scadente.

| Task | Modello | Perché |
|---|---|---|
| Leggere file, grep, list directory | **Haiku** | I/O puro, zero ragionamento |
| Scrivere test (pattern-based) | **Haiku** | Struttura ripetitiva, basso rischio |
| Code review checklist | **Haiku** | Regole fisse, no creatività |
| Componenti UI standard | **Sonnet** | Implementazione media complessità |
| Endpoint API / middleware | **Sonnet** | Logica server standard |
| Migration DB / query | **Sonnet** | Trasformazione strutturata |
| Self-correction (analisi errore) | **Sonnet** | Ragionamento necessario, non architetturale |
| Debug sistematico | **Sonnet** | Ipotesi → verifica, ciclo breve |
| Architettura sistema / ADR | **Opus** | Decisioni multi-sistema, alta posta |
| Audit sicurezza OWASP | **Opus** | High-stakes, nessun margine errore |
| AI/LLM engineering | **Opus** | Ragionamento complesso su catene di prompt |
| Requisiti vaghi → specifiche | **Opus** | Ampia comprensione del dominio |

**Regola pratica:** inizia sempre con Haiku per leggere e capire, poi scala al modello necessario per agire.

### Context Pruning — regole di contesto minimo

Non passare l'intero progetto a ogni agente. Ogni agente riceve solo ciò che serve per il suo task:

| Agente | Cosa riceve |
|---|---|
| Frontend | Solo i componenti e le pagine coinvolte + design tokens |
| Backend | Solo i file endpoint + middleware + contratti API da `ProjectMaster/knowledge/api_specs.json` |
| Database | Solo schema corrente + migration + query da ottimizzare |
| Reviewer | Solo il diff del task, non l'intera codebase |
| QA Tester | Solo il modulo da testare + i suoi input/output attesi |

**Boot sessione:** usare `./ProjectMaster/execution/context-boot.sh` invece di leggere 4-5 file separati — un solo output compatto.

**Self-correction:** usare `./ProjectMaster/execution/self-correct.sh` — gestisce il retry loop senza ripetere istruzioni all'LLM.

### GLM Delegation — Codifica a Costo Minimo

Per task di codifica ripetitiva (CRUD, test, scaffold, migration, DTO), delegare a GLM-4-Flash
invece di usare Claude. Claude monitora e valida, GLM esegue il lavoro pesante.

**Quando delegare a GLM (usa la skill `ingegneria/glm-delegate`):**
- Generazione boilerplate su pattern esistente
- Test unitari per funzioni già scritte
- Migration DB da schema definito
- Interfacce/tipi da specifiche JSON
- Serializer, validator, enum, costanti

**Quando NON delegare:**
- Architettura, scelta pattern, decisioni critiche
- Logica di business non ovvia
- Codice security-sensitive (auth, crittografia)
- Bug fix complessi

**Provider disponibili** (in ordine di costo):

| Provider | Modello default | Costo | Setup |
|---|---|---|---|
| `nvidia` | `z-ai/glm-5.1` | **$0** — 40 RPM | `NVIDIA_API_KEY` da build.nvidia.com |
| `openrouter` | `z-ai/glm-5.1` | pay-per-use | `OPENROUTER_API_KEY` da openrouter.ai |
| `zai` | `glm-4-flash` | ~$10/mese | `ZAI_API_KEY` da z.ai |

**Flusso:**
```bash
# 1. Prepara prompt in orchestration/glm-prompts/T01.md
# 2. Delega a GLM-5.1 via NVIDIA NIM (gratuito)
python3 ProjectMaster/execution/glm-call.py --provider nvidia \
  --prompt-file orchestration/glm-prompts/T01.md \
  --task T01 --agent frontend
# 3. Output in orchestration/glm-output/T01-frontend.md
# 4. Claude Reviewer (Haiku) valida e integra
# 5. Self-correction se necessario
./ProjectMaster/execution/self-correct.sh "npm test" "reviewer" "T01"
```

**Verifica modelli attivi:** `python3 ProjectMaster/execution/glm-call.py --provider nvidia --probe`

---

## Protocolli Z.ai — Autonomia e Self-Correction

Questi tre protocolli trasformano l'agente da assistente passivo a engine autonomo end-to-end.
Si attivano automaticamente durante la fase di esecuzione — nessuna conferma intermedia richiesta.

### RAG & KNOWLEDGE INTEGRATION

Prima di avviare qualsiasi task di programmazione, l'agente DEVE scansionare la cartella `/knowledge`.
Il codice generato deve allinearsi al 100% con i documenti presenti, senza inventare parametri o logiche esterne.

**Protocollo:**
1. Lista i file in `/knowledge` all'inizio del task
2. Identifica quali documenti sono rilevanti per il task corrente
3. Cita esplicitamente la fonte nel piano (`ProjectMaster/knowledge/PRD.md §3.2`, `ProjectMaster/knowledge/api_specs.json EP-01`, ecc.)
4. In caso di ambiguità: cerca prima in `/knowledge`, poi in `/directives`, infine chiedi all'utente

**Priorità fonti:**
```
ProjectMaster/knowledge/ > ProjectMaster/directives/ > CLAUDE.md > ragionamento autonomo
```

---

### TEST & SELF-CORRECTION PROTOCOL

Ogni volta che un agente scrive o modifica un file in `/execution`, esegue immediatamente il test.
Se il test fallisce, l'agente corregge e riprova — senza chiedere conferma all'utente.

**Ciclo:**
```
scrivi codice → esegui test → errore?
  ↓ NO: procedi
  ↓ SÌ: leggi log → deduci causa → correggi → ripeti (max 3 volte)
       dopo 3 fallimenti: genera report in /diagnostics e fermati
```

**Regole operative:**
- Non interrompere mai il ciclo per chiedere aiuto prima del 3° tentativo
- Non scusarsi: analizzare, correggere, riprocedere
- Aggiornare `ProjectMaster/orchestration/state.json > self_correction` a ogni ciclo
- Al 3° fallimento: generare `ProjectMaster/diagnostics/[timestamp]-[agente]-[task].json` e notificare l'utente

---

### DEVELOPMENT & PREVIEW

Al completamento della Task List, l'agente avvia l'ambiente di sviluppo e verifica la risposta.

**Sequenza obbligatoria:**
```bash
./ProjectMaster/execution/health-check.sh      # 1. Ambiente OK?
./ProjectMaster/execution/validate-build.sh    # 2. Build OK?
./ProjectMaster/execution/run-tests.sh         # 3. Test OK?
./ProjectMaster/execution/start_dev.sh         # 4. Preview — verifica Status 200
```

L'agente dichiara il task completato solo dopo che `start_dev.sh` ha confermato Status 200.
Se `start_dev.sh` non è applicabile (libreria, CLI, ecc.) i passi 1-3 sono comunque obbligatori.

---

## Framework D.O.E.

Il progetto segue il framework **D.O.E. (Directive, Orchestration, Execution)**.
Ogni layer ha responsabilità distinte e confini di scrittura non mescolabili.

### D — Directive Layer
**Cartella:** `ProjectMaster/directives/`
Contiene le regole di business, i vincoli di dominio, le policy operative del progetto.
- Aggiornabile solo dall'utente o dall'Architetto con conferma esplicita
- Read-only per gli agenti di implementazione (frontend, backend, database)
- Usa `ProjectMaster/directives/_template.md` per creare nuove direttive

### O — Orchestration Layer
**Cartella:** `ProjectMaster/orchestration/`
Gestisce la coordinazione del lavoro e lo stato del progetto a 3 tier:

| Tier | File | Vita | Contenuto |
|---|---|---|---|
| **Ephemeral** | `ProjectMaster/orchestration/state/ephemeral.md` | Una sessione | Obiettivo, task in corso, note rapide |
| **Journal** | `ProjectMaster/orchestration/state/journal.md` | Permanente (append-only) | Log di tutte le azioni completate |
| **Canonical** | `ProjectMaster/orchestration/state/canonical.md` | Permanente (versioned) | Stack, ADR, architettura stabile |

**Regola critica:** Prima di qualsiasi task con 2+ agenti, l'Orchestratore genera un piano in `ProjectMaster/orchestration/plans/[data]-[slug].json`. Il codice non viene toccato finché il piano non è approvato.

### E — Execution Layer
**Cartella:** `ProjectMaster/execution/`
Contiene script deterministici per verificare l'ambiente e validare il codice.

| Script | Cosa fa |
|---|---|
| `ProjectMaster/execution/health-check.sh` | Verifica che l'ambiente sia pronto |
| `ProjectMaster/execution/run-tests.sh` | Esegue i test e cattura l'esito |
| `ProjectMaster/execution/validate-build.sh` | Verifica che il progetto compili |

**Verification loop obbligatorio** — eseguire in quest'ordine prima di chiudere qualsiasi task:
```bash
./ProjectMaster/execution/health-check.sh && ./ProjectMaster/execution/validate-build.sh && ./ProjectMaster/execution/run-tests.sh
```

---

## Riferimenti rapidi

| Cosa | Dove |
|---|---|
| Stato sessione (ephemeral) | `ProjectMaster/orchestration/state/ephemeral.md` + `sessione.md` |
| Log azioni (journal) | `ProjectMaster/orchestration/state/journal.md` |
| Architettura stabile (canonical) | `ProjectMaster/orchestration/state/canonical.md` |
| Piani di task | `ProjectMaster/orchestration/plans/` |
| Knowledge Hub (RAG) | `ProjectMaster/knowledge/` |
| Direttive di business | `ProjectMaster/directives/` |
| Error reports | `ProjectMaster/diagnostics/` |
| Script di verifica | `ProjectMaster/execution/` |
| Agenti | `.claude/agents/` |
| Skill | `.claude/skills/` |
| Comandi | `.claude/commands/` |
| Configurazione | `.claude/settings.json` |
