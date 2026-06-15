"""
Usa il LLM per generare nuove skill Python da una richiesta in linguaggio naturale.
"""
import logging
import re

log = logging.getLogger("self_modify_agent")

_PROMPT = """\
Sei un assistente specializzato nella scrittura di Skill Python per Ari.
Scrivi SOLO codice Python, niente spiegazioni, niente markdown.

=== BASE CLASS ===
{base}

=== ESEMPIO ESISTENTE ===
{example}

=== RICHIESTA ===
{request}

=== REGOLE ===
- Classe: NomeSkill(Skill)
- Attributi: name = "snake_case",  description = "breve descrizione"
- match(): usa regex con pattern italiani, ritorna dict o None
- run(): esegui l'operazione, gestisci eccezioni, ritorna stringa leggibile
- Import solo dalla stdlib o psutil (già installato)
- Nessun markdown, nessun backtick, SOLO il codice

=== CODICE ===\
"""


async def generate_skill(user_request: str) -> dict | None:
    """Genera una nuova skill. Ritorna {class_name, skill_name, filename, content} o None."""
    from .self_modify import read_file
    from .llm import engine

    try:
        base    = read_file("skills/_base.py")
        example = read_file("skills/system_info.py")
    except Exception as e:
        log.error(f"Errore lettura template: {e}")
        return None

    prompt   = _PROMPT.format(base=base, example=example, request=user_request)
    messages = [{"role": "user", "content": prompt}]

    code = ""
    async for kind, token in engine.stream(messages, max_tokens=1500, thinking=False):
        if kind == "chunk":
            code += token

    code = _clean(code)
    if not code:
        return None

    class_m = re.search(r"class\s+(\w+Skill)\s*\(", code)
    name_m  = re.search(r'name\s*=\s*["\'](\w+)["\']', code)
    if not class_m:
        log.error("Classe Skill non trovata nel codice generato.")
        return None

    class_name = class_m.group(1)
    skill_name = name_m.group(1) if name_m else class_name.lower().replace("skill", "")
    filename   = f"skills/{skill_name}.py"

    return {
        "class_name": class_name,
        "skill_name": skill_name,
        "filename":   filename,
        "content":    code,
    }


def build_init_update(class_name: str, module_name: str, current_init: str) -> str:
    """Aggiorna skills/__init__.py aggiungendo import e istanza della nuova skill."""
    import_line = f"from .{module_name}  import {class_name}"
    instance    = f"    {class_name}(),"

    lines = current_init.splitlines()

    # Inserisci import dopo l'ultimo import esistente
    last_import = max(
        (i for i, l in enumerate(lines) if l.startswith("from .")),
        default=0,
    )
    lines.insert(last_import + 1, import_line)

    # Inserisci istanza prima di WebSearchSkill (ultima, priorità più bassa)
    for i, line in enumerate(lines):
        if "WebSearchSkill()" in line:
            lines.insert(i, instance)
            break

    return "\n".join(lines)


def _clean(code: str) -> str:
    code = code.strip()
    code = re.sub(r"^```(?:python|swift)?\n?", "", code)
    code = re.sub(r"\n?```$", "", code)
    return code.strip()


# ── Classificatore di richiesta ───────────────────────────────────────────────

_PYTHON_RE = re.compile(
    r"\b(?:skill|impara\s+a|aggiungi\s+(?:la\s+)?(?:capacit[àa]|abilit[àa]|funzionalit[àa])"
    r"|crea\s+(?:una\s+)?(?:nuova\s+)?skill)\b", re.I
)
_SWIFT_RE = re.compile(
    r"\b(?:pannello|finestra|pulsante|bottone|men[uù]|UI|interfaccia|visualizzazione"
    r"|widget|icona|colore|animazione|orb)\b", re.I
)
_VOICE_RE = re.compile(
    r"\b(?:voce|personalit[àa]|modo\s+di\s+parlare|tono|carattere|comportamento"
    r"|riscriviti|chi\s+sei|come\s+parli|stile)\b", re.I
)


def classify_request(text: str) -> str:
    """Ritorna: 'python_skill' | 'swift_ui' | 'personality'"""
    if _VOICE_RE.search(text):
        return "personality"
    if _SWIFT_RE.search(text):
        return "swift_ui"
    return "python_skill"


# ── Generatore Swift UI ───────────────────────────────────────────────────────

_SWIFT_PROMPT = """\
Sei un esperto di Swift/AppKit. Stai modificando AriApp, un'app macOS menu-bar-only.
Scrivi SOLO codice Swift, niente spiegazioni, niente markdown.

=== PANEL TEMPLATE (pattern da seguire) ===
{template}

=== FILE ESISTENTI ===
{file_list}

=== RICHIESTA ===
{request}

=== REGOLE ===
- Usa AriPanel (non NSPanel direttamente) — già definita nel progetto
- Registra il panel con SnapManager.shared.registerExtra(panel)
- Aggiungi al MenuBarManager tramite un metodo toggle
- Rispetta il dark theme (backgroundColor NSColor red:0.06 green:0.06 blue:0.10)
- Accent color: NSColor(red:0 green:0.85 blue:1 alpha:1)
- SOLO il codice Swift del/dei file da creare/modificare
- Separa file diversi con: // === FILENAME: NomeFile.swift ===

=== CODICE ===\
"""


async def generate_swift_change(user_request: str) -> list[dict] | None:
    """Genera modifiche Swift. Ritorna lista di {scope, rel_path, content, diff_hint}"""
    from .self_modify import read_scoped, list_swift_files
    from .llm import engine

    try:
        template  = read_scoped("swift", "StatsPanel.swift")
        file_list = "\n".join(list_swift_files())
    except Exception as e:
        log.error(f"Errore lettura template Swift: {e}")
        return None

    prompt   = _SWIFT_PROMPT.format(
        template=template, file_list=file_list, request=user_request
    )
    messages = [{"role": "user", "content": prompt}]

    raw = ""
    async for kind, token in engine.stream(messages, max_tokens=3000, thinking=False):
        if kind == "chunk":
            raw += token

    return _parse_swift_output(_clean(raw))


def _parse_swift_output(raw: str) -> list[dict]:
    """Divide l'output in {scope, rel_path, content} per ogni file."""
    changes = []
    parts   = re.split(r"//\s*===\s*FILENAME:\s*(\S+\.swift)\s*===", raw)

    if len(parts) == 1:
        # Singolo file — cerca il nome dalla prima riga o usa nome generico
        m = re.search(r"final class (\w+)", raw)
        name = (m.group(1) + ".swift") if m else "NewFeature.swift"
        changes.append({"scope": "swift", "rel_path": name, "content": raw.strip()})
    else:
        for i in range(1, len(parts), 2):
            filename = parts[i].strip()
            content  = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if content:
                changes.append({"scope": "swift", "rel_path": filename, "content": content})

    return changes


# ── Generatore personalità/voce ───────────────────────────────────────────────

_VOICE_PROMPT = """\
Stai modificando la personalità e il carattere di Ari, un AI assistant personale.
Scrivi SOLO il contenuto aggiornato del file, niente spiegazioni.

=== FILE CORRENTE: constitution/ari.md ===
{current}

=== RICHIESTA ===
{request}

=== REGOLE ===
- Mantieni il formato Markdown esistente
- Non rimuovere sezioni fondamentali (Chi sei, Carattere, Regole operative)
- Integra le modifiche richieste mantenendo la coerenza del personaggio
- SOLO il contenuto aggiornato del file

=== CONTENUTO AGGIORNATO ===\
"""


async def generate_personality_change(user_request: str) -> list[dict] | None:
    """Genera modifica a constitution/ari.md."""
    from .self_modify import read_scoped
    from .llm import engine

    try:
        current = read_scoped("constitution", "ari.md")
    except Exception as e:
        log.error(f"Errore lettura ari.md: {e}")
        return None

    prompt   = _VOICE_PROMPT.format(current=current, request=user_request)
    messages = [{"role": "user", "content": prompt}]

    content = ""
    async for kind, token in engine.stream(messages, max_tokens=2000, thinking=False):
        if kind == "chunk":
            content += token

    content = _clean(content)
    if not content:
        return None

    return [{"scope": "constitution", "rel_path": "ari.md", "content": content}]
