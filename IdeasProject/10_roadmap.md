# Athena 2.0 — Roadmap

## Principio

Ogni fase produce qualcosa di funzionante e usabile.
Non si passa alla fase successiva finche' la corrente non e' stabile.
Ogni fase ha un "Done quando..." verificabile su hardware reale.

---

## Mappa visiva

```
FASE 1 ──► FASE 2 ──► FASE 3 ──► FASE 4 ──► FASE 5
Foundation   LLM        Voce       Memoria    Skills
   │            │           │           │         │
   │            └───────────┴───────────┘         │
   │                        │                     ▼
   │                        └──────────────► FASE 6
   │                                        Knowledge
   │                                             │
   └─────────────────────────────────────────────┘
                                                 │
                                                 ▼
                                           FASE 7 ──► FASE 8 ──► FASE 9 ──► FASE 10
                                         Self-Mod    Home-HA   STT Swift    Polish
```

**Dipendenze obbligatorie:**
- FASE 2 richiede FASE 1 (canale WS operativo)
- FASE 3 richiede FASE 2 (serve LLM per dare senso alla voce)
- FASE 4 richiede FASE 2 (memoria senza LLM e' inutile)
- FASE 5 richiede FASE 2 + FASE 4 (skills usano LLM e contesto)
- FASE 6 richiede FASE 4 (vault usa il sistema memoria)
- FASE 7 richiede FASE 5 (self-modify e' una skill)
- FASE 8 richiede FASE 5 (HA e' una skill)
- FASE 9 e' indipendente — upgrade tecnico di FASE 3

---

## Concern trasversali (presenti in ogni fase)

Questi non sono fasi — sono requisiti che entrano da FASE 1 e crescono:

| Concern | Introdotto in | Dettaglio |
|---|---|---|
| **Logging** | FASE 1 | `athena.log` attivo dal primo giorno |
| **Config** | FASE 1 | `settings.json` leggibile da Swift e Python |
| **Health check** | FASE 1 | `/health` endpoint + self-check ogni 60s |
| **Privacy Mode** | FASE 1 | Pausa istantanea microfono e orb |
| **Auto-start** | FASE 1 | SMAppService per login item |
| **Error handling** | ogni fase | Segue `13_resilienza.md` per ogni componente |
| **Git versioning** | FASE 1 | Init repo, ogni modifica e' tracciata |

---

## FASE 1 — Foundation

**Obiettivo:** App Swift gira, daemon Python gira, si parlano.

**Deliverable:**
- Swift menu bar app + orb placeholder (cerchio statico, 4 colori per stato)
- Python FastAPI daemon con `/health` + logging attivo
- WebSocket Swift ↔ Python operativo (ping/pong + messaggi JSON)
- Swift lancia Python subprocess al boot, lo rilancia se crasha
- Hotkey globale (`Cmd+Shift+A`) attiva/nasconde orb
- Privacy Mode: click menu bar → pausa istantanea
- `settings.json` creato con valori default al primo avvio
- Input testo nell'orb → echo via WebSocket (no LLM)
- Git repo inizializzato (`git init`)
- Auto-start via `SMAppService`

**Done quando:** Scrivo "ciao" nell'orb, ricevo "ciao" di ritorno. Privacy Mode silenzia tutto.

---

## FASE 2 — LLM (Cervello base)

**Richiede:** FASE 1 completa

**Obiettivo:** Athena ragiona. Conversazione testuale funzionante.

**Deliverable:**
- Integrazione Ollama Python (Qwen3 14B)
- Streaming token → Swift aggiorna testo in real-time
- System prompt: `athena.md` (constitution) + `roby.md` (profilo)
- Working memory con sliding window (max 20 messaggi, sommario automatico)
- Orb Metal animato: idle / thinking / responding
- Gestione swap modelli 14B ↔ 32B con notifica e progress
- First run wizard: verifica Ollama, scarica modelli mancanti, permessi macOS
- Resilienza Ollama: retry 3x + fallback NVIDIA (opt-in)

**Done quando:** Conversazione testuale con streaming. Athena risponde in carattere. Orb si anima. Swap modelli funziona.

---

## FASE 3 — Voce

**Richiede:** FASE 2 completa

**Obiettivo:** Athena sente e parla.

**Deliverable:**
- Porcupine SDK: wake word "Athena" sempre attivo in Swift
- Registrazione utterance con VAD (silence detection, stop auto)
- whisper.cpp trascrizione via Python subprocess (it-IT, large-v3-turbo)
- Apple TTS output: voce Federica (Premium) it-IT
- Orb: cerchi espansivi durante ascolto, onde durante TTS (reattivi ad ampiezza audio)
- Modalita' silenziosa: solo testo, no audio
- Auto-pausa durante chiamate FaceTime/Telefono
- Resilienza STT: "Non ho capito, ripeti?" + fallback testo dopo 3 fallimenti

**Done quando:** Dico "Ehi Athena, che ore sono?" e risponde a voce.

---

## FASE 4 — Memoria

**Richiede:** FASE 2 completa

**Obiettivo:** Athena ricorda. Conosce Roby nel tempo.

**Deliverable:**
- ChromaDB embedded inizializzato in `/vault/athena/`
- Episodic memory: sommario sessione salvato al termine
- Semantic memory: estrazione fatti dalla conversazione
- `roby.md` sempre iniettato nel system prompt
- Memory retrieval: top-K chunk rilevanti prima di ogni risposta
- Resilienza ChromaDB: backup + re-index automatico su corruzione
- Health check: ChromaDB query test ogni 60s

**Done quando:** Athena ricorda conversazioni di 3 giorni fa e cita il contesto corretto.

---

## FASE 5 — Skills Core

**Richiede:** FASE 2 + FASE 4

**Obiettivo:** Athena fa cose concrete sul Mac.

**Deliverable:**
- SkillRegistry con hot reload (watchdog + importlib)
- Router: euristica keyword → skill (stadio 1) + LLM router (stadio 2)
- ConfirmView nell'orb per azioni che richiedono approvazione
- Skills implementate:
  - `mac_control`: apre file, app, URL via AppleScript
  - `web_search`: DuckDuckGo, ritorna sommario pulito
  - `file_ops`: leggi/crea file (conferma per modifica/delete)
  - `run_shell`: esegui comandi (conferma obbligatoria sempre)
  - `calendar`: leggi agenda Apple Calendar
  - `reminders`: crea promemoria Apple Reminders

**Done quando:** "Athena, cerca notizie su Ollama e aprimi Finder" — entrambe eseguite.

---

## FASE 6 — Knowledge Base

**Richiede:** FASE 4 completa

**Obiettivo:** Athena impara dai documenti che le dai.

**Deliverable:**
- watchdog su `Google Drive/AthenaInput/`
- VaultChunker: chunking heading-aware, overlap 50 token
- Pipeline: file rilevato → chunk → embed → ChromaDB → copia locale
- Notifica al completamento: "Ho studiato [nome file] — X chunk indicizzati"
- Re-index automatico su modifica file in AthenaInput/
- Athena scrive note in `/vault/athena/notes/` (sommari sessioni, cose apprese)
- Retrieval aumentato: documenti knowledge + memoria episodica + semantic

**Done quando:** Do un PDF tecnico ad Athena, lei lo studia, risponde a domande citando il documento.

---

## FASE 7 — Self-Modification Engine

**Richiede:** FASE 5 completa

**Obiettivo:** Athena propone e applica miglioramenti a se stessa.

**Deliverable:**
- `self_modify` skill: legge codice sorgente Python e Swift
- Generazione proposta diff (Qwen2.5 32B) con spiegazione italiana
- ConfirmView esteso: diff colorato + impatto + rischi
- Apply patch + esecuzione test automatici
- Git backup pre-modifica + rollback su fallimento (max 3 retry)
- Hot reload per modifiche Python skills
- xcodebuild + app restart per modifiche Swift (con stima tempo)
- Self-reflection settimanale: analisi sessioni → proposta 3 miglioramenti
- Log di ogni tentativo in `/diagnostics/`

**Done quando:** Athena trova un bug in `web_search`, propone fix, confermo, ricarica in <1s.

---

## FASE 8 — Home Assistant

**Richiede:** FASE 5 completa (e' una skill)

**Obiettivo:** Athena controlla la casa.

**Deliverable:**
- `home_assistant` skill: HTTP REST su HA locale
- Discovery automatica entita' (luci, clima, switch, sensori)
- Controllo vocale: accendi/spegni/dimmer/temperatura
- Query stato: "Athena, luci accese in casa?"
- Automazioni contestuali: "quando arrivo, accendi il soggiorno"
- Resilienza: HA offline → skill disabilitata gracefully

**Done quando:** "Athena, spegni le luci del corridoio" — eseguito.

---

## FASE 9 — STT Swift (upgrade latenza)

**Richiede:** FASE 3 completa (e' un upgrade, non una nuova feature)

**Obiettivo:** Trascrizione streaming parola-per-parola, latenza minima.

**Deliverable:**
- whisper.cpp xcframework integrato in Swift (sostituisce subprocess Python)
- Trascrizione streaming: ogni parola appare nell'orb mentre si parla
- Riduzione latenza: wake-to-first-token da ~700ms a ~400ms
- Orb aggiornato: testo live durante ascolto

**Done quando:** L'orb mostra le parole mentre sto ancora parlando.

---

## FASE 10 — Polish e Autonomia

**Richiede:** tutte le fasi precedenti

**Obiettivo:** Athena e' usabile quotidianamente, senza friction, piu' autonoma.

**Deliverable:**
- Settings UI completo: tutte le preferenze modificabili senza toccare JSON
- Modalita' silenziosa programmata per orario (es. 23:00-07:00)
- Statistiche uso: skills piu' usate, tempo risposta medio, modelli usati
- Backup automatico settimanale: ChromaDB + vault + settings
- Piper TTS come alternativa opzionale ad Apple TTS
- Notifiche macOS native per eventi, task completati, promemoria
- Aggiornamento self-reflection attiva: propone miglioramenti senza aspettare richiesta
- Multi-task: coda background tasks con notifica al completamento

**Done quando:** Athena e' parte della routine quotidiana. Zero friction.

---

## Note operative

**Non si lavora per date — si lavora per qualita'.**
Ogni fase e' completata quando il "Done quando" e' verificato su M1 Max reale, non in simulazione.

**Ordine priorita' assoluta:** FASE 1 → 2 → 3. Con queste tre Athena e' gia' utile.

**Parallelizzazione possibile:**
- FASE 3 e FASE 4 possono procedere in parallelo (dipendono entrambe da FASE 2, non tra loro)
- FASE 8 puo' essere fatta in parallelo con FASE 6 o 7 (e' una skill indipendente)
- FASE 9 puo' essere fatta in qualsiasi momento dopo FASE 3
