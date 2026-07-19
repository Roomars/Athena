# Ari — Modalità Desktop

Pannello chat flottante stile Claude Desktop, con aggiunta di:
- Artifacts (contenuto ricco rendered inline o come widget)
- Progetti (contesti isolati, come Claude Projects)
- Widget System (finestre floating Jarvis-style)
- MCP/Skills compatibility (stessa compatibilità di Claude Desktop)

---

## Layout generale

```
┌─────────────────────────────────────────────┐
│  ◉ Ari    [Progetto: Personale         ▼]  ✕ │  ← header: orb mini + switcher progetto + chiudi
│─────────────────────────────────────────────│
│                                             │
│  ╔═══════════════════════════════════════╗  │
│  ║  Tu                        14:32      ║  │
│  ║  Scrivi una funzione Python per...    ║  │
│  ╚═══════════════════════════════════════╝  │
│                                             │
│  Ari                                        │
│  Ecco la funzione:                          │
│  ┌─────────────────────────────────────┐    │
│  │ 🐍 codice.py          [↗] [⧉] [▶]  │    │  ← artifact inline
│  │ def process(data):                  │    │
│  │     return [x*2 for x in data]     │    │
│  └─────────────────────────────────────┘    │
│  Puoi chiamarla con `process([1,2,3])`.     │
│                                             │
│─────────────────────────────────────────────│
│ [📎] [🎤]  Scrivi ad Ari...               │  ← input area
│            [@ Menziona] [/ Skill]     [↵]  │
└─────────────────────────────────────────────┘
```

**Dimensioni pannello:** 420px wide, altezza dinamica (min 500px, max 85% schermo).
**Posizione default:** angolo basso-destra, ricordato tra sessioni.
**Trasparenza:** sfondo leggermente traslucido (vibrancy NSVisualEffectView).
**Always-on-top:** configurabile (default: no, solo orb è sempre visibile).

---

## Campo di inserimento

### Comportamento testo

| Azione | Effetto |
|---|---|
| `Enter` | Invia messaggio |
| `Shift+Enter` | Nuova riga (multiline) |
| `Cmd+V` | Incolla testo, immagini, o file |
| `Drag & Drop` | Rilascia file/immagini nell'area |
| `@` | Apre picker: menziona file del progetto corrente |
| `/` | Apre picker: richiama una skill direttamente |
| `↑` | Naviga messaggi precedenti (come shell) |

**Altezza:** auto-espandibile, da 1 riga a max 6. Sopra 6: scrollabile internamente.
**Placeholder:** "Scrivi ad Ari..." (scompare al primo carattere).

### Bottoni a sinistra dell'input

- **📎 Allega file:** picker macOS standard. Accetta: PDF, MD, TXT, immagini, codice, CSV.
- **🎤 Voce rapida:** registra senza wake word — comodo se sei già in chat mode.

### Bottoni contestuali (appaiono scrivendo `/`)

```
/ → picker verticale con tutte le skill disponibili
    Filtro real-time mentre scrivi
    Preview: nome + descrizione + shortcut
    Esempio: "/cerca" → skill web_search
              "/calcola" → skill math
              "/leggi" → skill file_ops
```

### Selezione testo nel pannello

Selezionando testo di una risposta precedente → mini toolbar:
- **Cita**: inserisce il testo selezionato come citazione nel prossimo messaggio
- **Copia**: copia negli appunti
- **→ Widget**: apre il testo selezionato come NoteWidget floating

---

## Artifacts

Gli artifacts sono blocchi di contenuto ricco, distinti dal testo normale.
Ari li genera automaticamente quando la risposta contiene contenuto strutturato.

### Tipi di artifact

| Tipo | Icona | Contenuto | Rendering |
|---|---|---|---|
| `code` | 🐍/⚡/🦀... | Codice sorgente | Syntax highlighting, Monaco-like |
| `markdown` | 📄 | Documento MD | Rendered con titoli, tabelle, liste |
| `html` | 🌐 | HTML/CSS/JS | WKWebView preview interattiva |
| `svg` | 🎨 | SVG grafica | Preview nativa |
| `json` | `{}` | Dati JSON | Tree view collassabile |
| `diff` | ±  | Git diff | Colori aggiunte/rimozioni |
| `chart` | 📊 | Dati → grafico | Swift Charts rendering |

### Intestazione artifact (sempre visibile)

```
┌─────────────────────────────────────┐
│ 🐍 utils.py          [↗] [⧉] [▶] [⋯] │
│─────────────────────────────────────│
│  ... contenuto ...                  │
└─────────────────────────────────────┘
```

**Azioni header:**
- **↗ Apri come Widget** — estrae in finestra floating sul desktop
- **⧉ Copia** — copia contenuto negli appunti
- **▶ Esegui** — solo per `code` (subprocess Python/shell, output inline)
- **⋯ Altro** → Salva file, Condividi, Chiudi

### Artifact inline vs Widget

**Inline (default):** artifact rimane nel pannello chat come parte della conversazione.
**Widget:** se premi ↗, l'artifact diventa un CodeWidget (o DocumentWidget, etc.) floating sul desktop. Il pannello mostra un placeholder: "📌 utils.py — aperto come widget".

L'utente può avere entrambi: artifact nel chat + widget sul desktop per tenerlo visibile mentre scrive.

---

## Progetti

Come Claude Projects: contesti isolati con knowledge base, system prompt e storia dedicata.

### Struttura di un progetto

```
~/.athena/projects/
  personale/
    knowledge/        ← file caricati dall'utente per questo progetto
    conversations/    ← storia conversazioni (JSON per sessione)
    system_prompt.md  ← istruzioni specifiche per Ari in questo contesto
    project.json      ← nome, descrizione, creato_il, ultimo_accesso
  lavoro/
    knowledge/
    ...
  athena_default/     ← progetto di default (sempre presente)
    knowledge/        ← qui va la knowledge globale (vault)
    ...
```

### Switcher progetto (dropdown nel header)

```
[Progetto: Personale ▼]
  → Personale             ← corrente (checkmark)
  → Lavoro
  → Codice Athena
  → + Nuovo progetto...
  → Gestisci progetti...
```

Cambiare progetto: la conversazione si azzera (o si mette in pausa), si carica il nuovo contesto.
La working memory è isolata per progetto.

### Creare un nuovo progetto

```
+ Nuovo progetto...
  → Nome: [__________]
  → Descrizione: [__________]
  → System prompt: [__________] (opzionale — "Rispondimi sempre come un senior dev")
  → Carica file knowledge: [📎 Allega]
  → Crea
```

### Knowledge per progetto

Ogni progetto ha la sua cartella `knowledge/`. L'utente ci può caricare:
- File di codice (Ari li legge come contesto)
- Documenti PDF/MD
- URL da indicizzare (watchdog li scarica e indicizza)

Ari usa solo la knowledge del progetto attivo + la knowledge globale (athena_default).

---

## Widget System (Jarvis-style)

Quando Ari "crea qualcosa" — codice, documento, pagina web, grafico, note — può farlo apparire come finestra floating sul desktop invece che solo nel pannello chat.

### Tipi di widget

| Widget | Contenuto | Trigger automatico |
|---|---|---|
| **CodeWidget** | Codice con syntax highlighting | Ari scrive codice > 10 righe |
| **DocumentWidget** | Documento MD rendered | Ari scrive documento strutturato |
| **WebWidget** | WKWebView HTML preview | Artifact di tipo `html` |
| **TerminalWidget** | Output shell in tempo reale | Ari esegue un comando lungo |
| **ImageWidget** | Immagine / grafico / SVG | Artifact di tipo `svg`, `chart`, immagine |
| **NoteWidget** | Blocco note libero, editabile | Su richiesta o selezione testo |
| **BrowserWidget** | Pagina web (risultato ricerca) | Skill web_search → apri pagina |
| **DiffWidget** | Git diff colorato | Self-modification proposal |

### Anatomia di un widget

```
┌─────────────────────────────────────────┐
│ 🐍 utils.py          [_][□][✕]         │  ← barra titolo draggable
│─────────────────────────────────────────│
│                                         │
│  def process(data):                     │  ← contenuto
│      return [x*2 for x in data]        │
│                                         │
│─────────────────────────────────────────│
│ [▶ Esegui]  [⧉ Copia]  [💾 Salva]     │  ← toolbar contestuale
└─────────────────────────────────────────┘
```

**Dimensioni default:** 500×400px, ridimensionabile dagli angoli/bordi.
**Livello finestra:** `.floating` — sopra le app normali, sotto i pannelli di sistema.
**Barra titolo:** draggable per spostare il widget ovunque nel desktop.

### Comportamento mouse

**Clic sinistro drag** sulla barra titolo → sposta widget.
**Clic bordo/angolo** → ridimensiona.
**Doppio clic** sulla barra titolo → massimizza/ripristina.
**Clic destro** → context menu (vedi sotto).
**Cmd+W** su widget in focus → chiudi.

### Context menu (tasto destro sul widget)

```
右 Chiudi
─────────────────
📌 Pinna (non chiudere mai)
□  Flottante / Fisso su schermo
─────────────────
⧉  Duplica
📤 Esporta...
↩  Invia in chat (inserisce come citazione)
─────────────────
⚙  Impostazioni widget...
```

**Pinna:** il widget sopravvive al riavvio di Ari. Viene riaperto automaticamente alla prossima sessione con il contenuto salvato.
**Fisso:** rimane in posizione anche se sposti altre finestre (come un quadro sul desktop).

### Widget Manager

Accessibile da: menu bar → "Widget" o hotkey `Cmd+Shift+W`.

```
┌─────────────────────────────────────────┐
│ Widget aperti                       [✕] │
│─────────────────────────────────────────│
│ 🐍 utils.py          [Vai] [📌] [✕]   │
│ 📄 Schema DB         [Vai] [📌] [✕]   │
│ 🌐 Preview homepage  [Vai] [📌] [✕]   │
│─────────────────────────────────────────│
│ Widget pinnati (persistono al riavvio)  │
│ 📄 Note lavoro       [Vai] [unpin] [✕] │
└─────────────────────────────────────────┘
```

### Quando Ari apre automaticamente un widget

Ari non apre widget automaticamente senza avvisi — l'utente sceglie.
**Default:** tutto appare inline nel pannello chat.
**Trigger widget:**
1. Utente preme ↗ su un artifact
2. Utente dice "Metti il codice in una finestra separata"
3. Task lungo in background → TerminalWidget si apre per mostrare l'output
4. Self-modification proposal → DiffWidget sempre aperto (non inline)

**Eccezione DiffWidget:** quando Ari propone una modifica al proprio codice, la proposta appare SEMPRE come DiffWidget floating + card di conferma nel pannello — non inline, per distinguerla dalla conversazione normale.

### Salvataggio posizioni

Le posizioni di tutti i widget vengono salvate in `~/.athena/widget_state.json` ogni 30s.
Al prossimo avvio: i widget pinnati vengono riaperti alle stesse coordinate.

---

## Skill e capacità — acquisizione e connettori

Dettaglio completo in [04_skills.md](04_skills.md). Sintesi:

### Acquisizione skill da Claude Desktop

Ari può leggere la configurazione MCP di Claude Desktop, scansionare i server disponibili e **generare wrapper Python nativi** che salva in `/skills/imported/`. La skill diventa di Ari — permanente, offline, modificabile.

Flusso: "Ari, acquisisci le skill di Claude Desktop" → lista tool trovati → conferma → file `.py` generati → hot reload → git commit.

### MCP Server (per tool esterni pesanti)

Quando un tool richiede un processo esterno persistente (browser headless, remote FS, ecc.) Ari può connettersi in runtime via JSON-RPC. Configurati in `settings.json > mcp_servers`.

### API Connectors (integrazione diretta)

Skill specializzate in `/skills/connectors/` che parlano direttamente con API esterne senza intermediari. Credenziali in macOS Keychain (mai in settings.json o in git).

Connector pianificati: Notion, GitHub, Spotify, Telegram, Home Assistant, Obsidian, Google Calendar, Linear.

### Nel picker `/` del pannello Desktop

- Skill native → icona del dominio (🔍 ricerca, 📁 file, ecc.)
- Skill importate da MCP → 🔌
- API Connectors → icona del servizio

---

## Shortcut da definire nel pannello Desktop

| Shortcut | Azione |
|---|---|
| `Cmd+N` | Nuovo messaggio / pulisci chat |
| `Cmd+Shift+P` | Switcher progetto |
| `Cmd+Shift+W` | Widget Manager |
| `Cmd+K` | Command palette (cerca skill, progetto, widget) |
| `Cmd+,` | Impostazioni pannello |
| `Esc` | Chiudi pannello (torna solo orb) |
| `/` | Skill picker (dentro il campo input) |
| `@` | File picker progetto (dentro il campo input) |

---

## Decisioni

| # | Decisione | Scelta |
|---|---|---|
| D35 | Artifacts inline | Sì, come Claude Desktop — rendered nel pannello |
| D36 | Widget system | Sì — ↗ su artifact apre finestra floating draggable |
| D37 | Tasto destro widget | Sì — context menu: chiudi, pinna, esporta, invia in chat |
| D38 | MCP compatibility | Sì — MCP client Python legge config Claude Desktop |
| D39 | Progetti | Sì — contesti isolati con knowledge e system prompt |
| D40 | DiffWidget obbligatorio | Self-modification proposta sempre come widget, mai inline |
| D41 | Widget posizioni | Salvate in widget_state.json, ripristinate al riavvio per widget pinnati |
