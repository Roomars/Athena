# Ari — Feature Jarvis

## Principio

Jarvis non risponde — anticipa, monitora, agisce.
Ari non è un chatbot con voce. È un'intelligenza che vive con te.

---

## PROATTIVITÀ — Ari non aspetta che tu chieda

### Morning Briefing
Ogni mattina, al primo accesso o all'orario configurato:
"Buongiorno. Hai 2 appuntamenti oggi: standup alle 9, call con Marco alle 15.
La build di Misterlab ha fallito stanotte — errore nel deploy. 
3 email con alta priorità in attesa."

Fonti: Apple Calendar, Mail, CI/CD hooks, notizie configurate.

### Alert contestuali automatici
- "Non mangi da 8 ore" (se hai un timer pasti configurato)
- "Hai una call tra 15 minuti — stai ancora codificando"
- "Questo task è aperto da 3 giorni senza aggiornamenti"
- "La PR #47 ha ricevuto un commento da revisionare"
- "Ollama usa il 90% della RAM — vuoi chiudere qualcosa?"

### Intelligence proattiva
- Monitora feed configurati (blog tech, notizie settore, repo GitHub seguiti)
- "Ho trovato una soluzione al problema che stavi cercando ieri su Stack Overflow"
- "Qwen ha rilasciato una nuova versione — vuoi aggiornare?"
- "Ho letto i 3 PDF che hai messo in AthenaInput — vuoi il riassunto?"

### Project monitoring
Ari conosce i tuoi progetti e li monitora passivamente:
- Build status (CI/CD webhooks)
- Commit recenti (git log)
- Issue aperti
- Scadenze nel backlog

---

## SCREEN AWARENESS — Ari vede quello che vedi

Con permesso Screen Recording (già richiesto):

### Analisi contestuale
- "Ari, cosa sta succedendo in questa finestra?" → Ari vede lo schermo e spiega
- Analisi automatica del contesto: se sei in Xcode → risponde come tecnico Swift
- Se sei in Figma → risponde come designer
- Se sei in un PDF → sa di cosa parli senza che tu descriva il documento

### OCR realtime
- "Ari, leggi questo testo" → OCR sul contenuto visibile
- Drag di un'area dello schermo → Ari trascrive e analizza
- Screenshot → analisi immediata

### Vision (MLX-vlm)
- Analisi immagini allegate
- "Cosa c'è in questa foto?"
- "Analizza questo screenshot di errore"
- "Descrivi il layout di questa UI"

---

## CONSAPEVOLEZZA CONTESTUALE

### App attiva
Ari sa quale app stai usando e adatta le risposte:
- Xcode aperto → risponde con Swift/codice
- Terminal → preferisce comandi shell
- Browser → può leggere la pagina via screen awareness
- Figma → risponde con linguaggio design

### Stato emotivo (voce)
Dal tono della voce durante i messaggi vocali:
- Stressato → risposte brevi, senza fronzoli, azione diretta
- Rilassato → può essere più esaustivo, aggiungere contesto
- Stanco (orario tardo) → suggerisce di fermarsi, brevità

### Memoria del flusso
Sa dove eri rimasto: "Stavi lavorando su [task] ieri sera — vuoi riprendere?"
Sa cosa hai fatto oggi: timeline implicita della sessione.

---

## MODALITÀ OPERATIVE

### Quick mode (default per richieste semplici)
- Usa Qwen3 14B (già in RAM)
- Risposta in <3 secondi
- No ragionamento esteso
- Per: domande semplici, comandi, lookup rapidi

### Deep mode (ragionamento esteso)
- Usa Qwen2.5 32B (swap, ~20s per caricare)
- Prende il tempo che serve
- Chain-of-thought interno prima di rispondere
- Per: architettura, debug complesso, decisioni importanti, analisi

### Background mode (task asincroni)
- Ari esegue mentre tu fai altro
- Notifica macOS quando finito
- Orb nel notch mostra indicatore attività
- Per: indicizzare documenti, ricerca approfondita, elaborazione lunga

### Focus mode
- "Ari, focus mode" → blocca notifiche non urgenti, risponde solo se chiamata
- Timer Pomodoro opzionale integrato
- "Ari, break" → suggerisce pausa, apre musica rilassante

---

## CONTROLLO AMBIENTE (Mac + Casa)

### Mac
- **Musica:** "Ari, metti qualcosa per concentrarsi" → Apple Music playlist
- **Volume/Luminosità:** "Ari, abbassa il volume" → controllo sistema
- **App:** "Ari, apri Xcode sul progetto Misterlab" → mac_control
- **System monitor:** "Ari, perché il Mac è lento?" → top processes, RAM, CPU

### Casa (FASE 8 - Home Assistant)
- Luci, clima, switch → già pianificato
- Contesto automatico: tardi la sera → "Abbasso le luci?"

---

## PERSONALITÀ E MEMORIA RELAZIONALE

### Carattere (invariante)
Ari è diretta, concreta, leale. Non adulatoria, non robotica.
Ha un senso dell'umorismo asciutto quando il contesto lo permette.
Non si presenta mai. Risponde direttamente.

### Evoluzione nel tempo
- Impara come Roby preferisce ricevere le risposte
- Se Roby tronca sempre le risposte lunghe → smette di essere prolissa
- Se Roby fa sempre domande tecniche profonde → sa che può essere più tecnica
- Ricorda preferenze esplicite: "Ari, da ora rispondi sempre in italiano tecnico"

### Memoria personale
- Cose dette nelle conversazioni: "hai detto che preferisci X"
- Compleanni, date importanti menzionate
- Progetti con storia: "la prima volta che hai parlato di Misterlab era il..."
- Inside jokes o frasi ricorrenti

### Tono adattivo
- Con Roby rilassato: può avere più personalità
- Con Roby di fretta: chirurgica, zero padding
- Mai sycophantic: non dice "ottima domanda!" o "certamente!"

---

## INTERFACCIA SPAZIALE

### Espansione contestuale dell'orb
Quando Ari deve mostrare dati, l'orb si espande in un pannello ricco:
- Grafici (matplotlib output renderizzato)
- Tabelle
- Codice con syntax highlighting
- Timeline, diagrammi

### Gesture (Chat mode)
- **Swipe** sul pannello → scorre la storia
- **Drag file** → allega documento
- **Cmd+K** → command palette (cerca nella storia, cambia modalità)

---

## GESTIONE SUB-AGENTI

### Tipo A — Parallelismo interno
Per task divisibili in sotto-task indipendenti, Ari li esegue in parallelo:
```
"Ricerca i migliori framework Swift per animazioni"
  → Sub-task 1: web_search "SwiftUI animation frameworks 2026"
  → Sub-task 2: web_search "Metal animation libraries macOS"
  → Sub-task 3: web_search "Lottie Swift integration"
  → Sintetizza i 3 risultati in risposta unica
```
Stessa istanza, thread separati (asyncio Python).

### Tipo B — Istanze parallele (task pesanti)
Per task molto complessi che richiedono ragionamento separato:
```
"Analizza questi 10 PDF e trova le contraddizioni"
  → Istanza 1: analizza PDF 1-3
  → Istanza 2: analizza PDF 4-6
  → Istanza 3: analizza PDF 7-10
  → Ari principale sintetizza i 3 report
```
Più Ollama instances in parallelo, RAM permitting.

### Quando usare quale
- Task parallelizzabili con 3+ ricerche indipendenti → Tipo A (sempre)
- Task che richiedono ragionamento profondo su corpus separati → Tipo B (solo se RAM sufficiente)
- La scelta è automatica — Ari decide basandosi sulla natura del task

---

## GESTIONE SKILL (UI)

### Pannello skills (in settings)
Lista di tutte le skills attive con:
- Nome, descrizione, versione
- Status: attiva / disabilitata / in aggiornamento
- Toggle per abilitare/disabilitare
- Log ultimi utilizzi
- "Aggiorna" per hot reload manuale

### Ari parla delle sue skills
"Ari, cosa sai fare?" → lista skills attive in italiano
"Ari, aggiungi la skill per Spotify" → Ari la propone e scrive

---

## GESTIONE PROGETTI

### Concetto
Progetti separati = contesti separati. Come i "Projects" di Claude.
Ogni progetto ha: propria memoria, propri documenti, proprio system prompt.

```
Progetti:
├── [Default] — conversazione generale
├── Misterlab — app calcio, Next.js, Supabase
├── Athena — il progetto stesso
├── Casa — domotica, Home Assistant
└── [nuovo progetto]
```

### Switch progetto
"Ari, passa al progetto Misterlab" → carica contesto Misterlab
Orb o chat mostra progetto attivo nell'header.

### Per ogni progetto
- Documenti dedicati nel vault
- System prompt aggiuntivo (chi sei in questo contesto)
- Skills rilevanti attivate/disattivate per progetto
- Storia conversazione separata

---

## INTELLIGENZA OPERATIVA (pattern da ONEPUNCHMAN411 e OpenJarvis)

### Complexity Router — latenza adattiva

Prima di chiamare MLX-lm, il daemon classifica la query in <10ms (regex + lunghezza + segnali semantici):

| Tier | Esempi | Token budget | Modalità |
|---|---|---|---|
| trivial | "che ore sono", "apri Spotify" | 512 | no chain-of-thought |
| simple | "scrivi una email breve" | 1024 | standard |
| moderate | "spiega questo codice" | 4096 | standard |
| complex | "architettura per questo sistema" | 8192 | chain-of-thought |
| very_complex | "analizza 10 documenti e trova contraddizioni" | 16384 | sub-agenti |

Per Qwen3 "thinking mode": budget x2. Il risparmio su task triviali è la differenza tra 300ms e 3 secondi.

### Strategy Memory — router che impara

SQLite in `~/.ari/strategy_memory.db`. Per ogni invocazione:
```
(task_category, skill_used, latency_ms, tokens_total, success) → registrato
```
Il router usa le metriche storiche per scegliere il percorso più veloce per quel tipo di task.
Dopo 50 esecuzioni, il routing è ottimizzato per le abitudini di Roby, non per parametri generici.

### Skill Overlay — few-shot auto-appresi

Ogni skill può avere `~/.ari/skills/<nome>/overlay.yaml` con esempi di esecuzioni passate:
```yaml
examples:
  - input: "cerca notizie su Swift 6"
    output: "Ho trovato 5 articoli rilevanti..."
    quality_score: 0.95
```
Top-3 esempi iniettati come few-shot nel prompt della skill. Nessun fine-tuning — la qualità migliora usando la skill.

### Loop Guard — anti-deadlock per self-modification

Tre meccanismi paralleli per il daemon Python:
1. **Hash identità**: se la stessa chiamata identica si ripete 3 volte → blocca
2. **Ping-pong detection**: se il flusso A→B→A→B viene rilevato in finestra scorrevole → blocca al secondo ciclo
3. **Tool budget**: ogni skill può essere invocata max 5 volte nello stesso loop agentico

Critico per il self-modification engine: senza questo, "leggi codice → analizza → riscrivi → rileggi" può girare all'infinito.

### Permission Store — autonomia progressiva

`~/.ari/permissions.yaml` — l'utente "insegna" le preferenze una volta sola:
```yaml
always_approve:
  - "luci:spegni_notte"
  - "musica:concentrazione"
  - "mail:leggi_inbox"
always_deny:
  - "file_ops:delete"
  - "git:push"
```
Azioni ricorrenti approvate → Ari le esegue autonomamente.
Azioni irreversibili o di primo contatto → sempre in coda di approvazione.
L'utente può aggiornare il file o dire "Ari, chiedi sempre prima di spegnere le luci".

### ScreenWatcher self-throttle — proattività non invasiva

Il proactive agent si auto-regola in base al comportamento di Roby:
- 3 suggerimenti scartati consecutivi → intervallo polling x2
- 5 suggerimenti scartati → monitoring in pausa (Ari avvisa: "Smetto di suggerire per ora")
- Riprende al successivo task change o su comando esplicito
- `quiet_apps`: lista app dove Ari tace sempre (Zoom, FaceTime, fullscreen game, Presentation)

Senza questo meccanismo un assistant proattivo diventa spam in 10 minuti.

---

## MORNING BRIEFING (format ottimizzato TTS)

Cron alle 06:00. Format preciso — ottimizzato per Federica TTS:

**Regole:**
- Mai numeri grezzi → sempre interpretazioni: "HRV 53" diventa "hai dormito bene"
- Max 250 parole, zero markdown, zero emoji, zero bullet visivi
- Frasi complete, ritmo naturale parlato
- Ordine prescritto: saluto + priorità → calendario → messaggi (triage) → salute → mondo → chiusura

**Esempio:**
"Buongiorno. La settimana inizia bene sul fronte dei progetti.
Hai uno standup alle 9 e una call con Marco alle 15 — entrambe brevi.
Hai dormito bene stanotte. Tre email in attesa, due sono urgenti: una da Paolo sul deploy e una da GitHub sul PR 47.
Nulla di rilevante nel feed tech. A dopo."

---

## EMERGENZA / SICUREZZA

### Rilevamento crisi
Se Ari rileva pattern di distress nel linguaggio (iterazione su parole negative, tono molto basso):
- Non ignora
- Domanda: "Stai bene?"
- Non fa da terapeuta — suggerisce risorse se appropriato

### Kill switch
"Ari, fermati" → stop immediato di qualsiasi task in corso
`Cmd+Shift+Esc` → hard stop, Privacy Mode istantanea

### Log trasparente
Tutto quello che Ari fa è loggato e leggibile:
"Ari, cosa hai fatto oggi?" → lista azioni, skill usate, documenti letti
