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
    code = re.sub(r"^```(?:python)?\n?", "", code)
    code = re.sub(r"\n?```$", "", code)
    return code.strip()
