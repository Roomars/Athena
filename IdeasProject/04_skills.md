# Athena — Skills System

## Principio

Le skills sono le "mani" di Athena — tutto ciò che può fare oltre a rispondere.
Ogni skill è un modulo Python isolato con interfaccia standard.
Athena può aggiungere nuove skills, modificarle, ritirarle — senza toccare il core.

---

## Struttura di una skill

```
skills/
├── mac_control.py
├── web_search.py
├── home_assistant.py
├── file_ops.py
├── calendar.py
├── reminders.py
└── self_modify.py   ← skill speciale, vedi 05_self_improvement.md
```

Ogni file skill segue questa interfaccia:

```python
# skills/web_search.py

SKILL_META = {
    "name": "web_search",
    "description": "Cerca informazioni su internet via DuckDuckGo",
    "triggers": ["cerca", "trova", "cosa è", "notizie"],
    "requires_internet": True,
    "requires_confirmation": False,
}

async def execute(params: dict) -> dict:
    """
    params: { "query": "cosa cercare" }
    returns: { "success": bool, "result": str, "error": str | None }
    """
    ...
```

---

## Skill Registry

Il registry è il catalogo di tutte le skills attive.
Caricato all'avvio, aggiornato a caldo tramite hot reload.

```python
class SkillRegistry:
    skills: dict[str, SkillModule]
    
    def load_all(self): ...          # carica da /skills/*.py
    def reload(self, name: str): ... # hot reload singola skill
    def list(self) -> list[str]: ... # lista skills attive
    def execute(self, name, params): ...
```

---

## Hot reload

Quando una skill viene modificata (da Athena stessa o da Roby):

```
watchdog rileva modifica file
    ↓
SkillRegistry.reload("nome_skill")
    ↓
importlib.reload(module)
    ↓
Nuova versione attiva in meno di 1 secondo
    ↓
Nessun riavvio del daemon Python necessario
```

---

## Skills core (da implementare subito)

| Skill | Cosa fa | Conferma richiesta |
|---|---|---|
| `mac_control` | Apre file/app/URL, script AppleScript | No per aperture, Sì per delete |
| `web_search` | DuckDuckGo, ritorna sommario | No |
| `file_ops` | Leggi, crea, modifica file locali | Sì per modifica/delete |
| `home_assistant` | Luci, clima, dispositivi via HA API | No per luci, Sì per allarme |
| `calendar` | Leggi/crea eventi Apple Calendar | Sì per creazione |
| `reminders` | Crea promemoria Apple Reminders | No |
| `run_shell` | Esegui comandi shell | Sì sempre |
| `self_modify` | Propone modifiche al codice di Athena | Sì sempre |

---

## Routing — come Athena sceglie la skill

Il router usa un approccio a due stadi:

**Stadio 1 — Euristica locale (senza LLM):**
Parole chiave nel testo → skill candidate.
Es: "apri", "lancia" → mac_control. "cerca", "cosa è" → web_search.
Veloce, zero latenza, risolve il 70% dei casi.

**Stadio 2 — LLM router (solo se stadio 1 ambiguo):**
Qwen3 14B riceve: input + lista skills + descrizioni.
Output: skill scelta + parametri estratti.

---

## Permessi e conferme

Tre livelli di autonomia per ogni skill:

| Livello | Comportamento |
|---|---|
| `auto` | Esegue senza chiedere |
| `confirm` | Mostra cosa farà, aspetta "sì" |
| `explicit` | Richiede sempre conferma + descrizione dettagliata |

Default conservativo: `confirm` per qualsiasi azione che modifica file o sistema.

---

## Skills generate da Athena

Quando Athena propone una nuova skill:
1. Genera il codice Python con il formato standard
2. Lo mostra a Roby con spiegazione
3. Aspetta conferma
4. Lo salva in `/skills/`
5. watchdog lo rileva → hot reload automatico
6. Git commit automatico con messaggio descrittivo

La nuova skill è subito disponibile senza riavvio.

---

## Acquisizione skill da Claude Desktop (MCP → skill native)

Ari non si connette agli MCP server di Claude come proxy runtime.
**Ari acquisisce le skill**: legge le definizioni dai server MCP, genera wrapper Python nel suo formato standard, le salva in `/skills/imported/` — diventano capacità proprie, permanenti, offline.

### Flusso di acquisizione

```
Roby: "Ari, acquisisci le skill di Claude Desktop"
    ↓
Ari legge claude_desktop_config.json
    ↓
Ari avvia temporaneamente ogni MCP server, chiede lista tool (tools/list)
    ↓
Ari genera un wrapper Python per ogni tool:
    skills/imported/mcp_filesystem__read_file.py
    skills/imported/mcp_browser__screenshot.py
    ...
    ↓
Mostra a Roby: "Trovate 12 skill da acquisire: [lista con descrizione]"
    ↓
Roby: "Acquisisci tutte" / seleziona singole
    ↓
Hot reload → skill immediatamente attive
    ↓
Git commit: "feat: acquired 12 skills from Claude Desktop MCP"
```

### Formato wrapper generato

```python
# skills/imported/mcp_filesystem__read_file.py
# Auto-generato da Ari — acquisita da MCP server: filesystem
# Sorgente: claude_desktop_config.json > mcp-server-filesystem

SKILL_META = {
    "name": "mcp_filesystem__read_file",
    "display_name": "Leggi file",
    "description": "Legge il contenuto di un file dal disco",
    "triggers": ["leggi", "apri file", "mostrami il file"],
    "source": "mcp:filesystem",          # traccia l'origine
    "acquired_on": "2026-06-14",
    "requires_confirmation": False,
}

async def execute(params: dict) -> dict:
    """Chiama il MCP server filesystem via JSON-RPC."""
    result = await mcp_call("filesystem", "read_file", params)
    return {"success": True, "result": result}
```

Il wrapper è codice Python reale — Ari (o Roby) può modificarlo, migliorarlo, specializzarlo.
Non è un bridge runtime: se il MCP server viene disinstallato, Ari può riscrivere l'implementazione in Python puro.

### Skill store condiviso

In futuro: skill scritte da altri utenti Ari (formato YAML + Python) possono essere importate direttamente, come un "marketplace" locale. Il formato standard lo permette senza ulteriori adattamenti.

---

## MCP Server e API Connectors

Due modi per espandere le capacità di Ari oltre le skill Python:

### MCP Server (runtime, per tool pesanti)

Per server MCP che richiedono un processo esterno persistente (browser headless, filesystem remoto, ecc.):
Ari può connettersi in runtime via JSON-RPC — utile quando il tool non ha senso wrappare in Python puro.

```json
// settings.json
"mcp_servers": {
  "browser": {
    "command": "npx",
    "args": ["@modelcontextprotocol/server-puppeteer"]
  }
}
```

Differenza con l'acquisizione: il server gira, Ari lo chiama, ma non genera una skill locale.
Usato per tool grandi/esterni (browser automation, accesso a sistemi remoti).

### API Connectors (integrazione diretta)

Skill specializzate che parlano direttamente con API esterne — senza MCP, senza intermediari.
Ogni connector è un file Python in `/skills/connectors/` con auth gestita via keychain macOS.

| Connector | API | Cosa fa |
|---|---|---|
| `notion` | Notion API | Legge/scrive pagine e database Notion |
| `github` | GitHub REST | Issue, PR, repo, commit |
| `spotify` | Spotify Web API | Controllo musica, playlist, brani |
| `telegram` | Bot API | Riceve/invia messaggi Telegram |
| `home_assistant` | HA REST | Luci, clima, dispositivi (già pianificato) |
| `obsidian` | Local REST Plugin | Legge vault Obsidian se attivo |
| `google_calendar` | Google API | Legge/crea eventi (alternativa ad Apple Calendar) |
| `linear` | Linear API | Issue e task di progetto |

**Gestione credenziali:** nessuna chiave hardcodata.
Tutte le API key in macOS Keychain via `keyring` Python — mai in `settings.json`, mai in git.

```python
# Lettura credenziale
import keyring
token = keyring.get_password("ari.connector.notion", "api_key")
```

**Aggiunta connector:** Ari propone automaticamente nuovi connector se rileva che Roby usa spesso un servizio. Roby autorizza, fornisce la chiave, Ari la salva nel keychain e attiva il connector.
