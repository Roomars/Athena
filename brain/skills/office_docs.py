"""
Skill: crea e modifica documenti Office (Word/Excel/PowerPoint) tramite OfficeCLI.

Trigger:
  - "crea una presentazione/powerpoint su ..."
  - "genera un documento/file word con ..."
  - "crea un foglio/file excel con ..."
  - "modifica/aggiorna il file X.pptx/docx/xlsx con ..."

Pattern architetturale: "LLM pianifica, codice esegue" (come self_modify_skill).
OfficeCLI ha comandi ricchi e componibili (create/add/set/view, indirizzamento
path-based tipo /slide[1]/shape[2]) non mappabili 1:1 con regex fisse: quindi
la skill chiede all'LLM di generare la sequenza di comandi come lista JSON, poi
li esegue lei stessa dopo averli validati per sicurezza.

Dipendenza esterna: binario `officecli` (github.com/iOfficeAI/OfficeCLI,
Apache 2.0, self-contained). NON viene installato automaticamente: se assente,
la skill ritorna un messaggio chiaro all'utente.

Sicurezza: ogni file può essere scritto SOLO dentro ~/Documents/Ari-Output/.
"""
import re
import json
import shutil
import logging
import asyncio
import subprocess
from pathlib import Path

from ._base import Skill

log = logging.getLogger("skill.office_docs")

# ---------------------------------------------------------------------------
# Regex di trigger
# ---------------------------------------------------------------------------

# Verbo d'azione + (opzionale determinante/quantificatore) + tipo documento.
# Copre creazione ("crea/genera/fai/prepara") e modifica ("modifica/aggiorna/
# cambia"). Il tipo di documento è catturato per inferenza pptx/docx/xlsx.
_TRIGGER_RE = re.compile(
    r"\b(?:crea|genera|fai|prepara|realizza|modifica|aggiorna|cambia|edita)\b"
    r"[^\n]*?\b(?:"
    r"presentazion[ei]|powerpoint|power\s*point|slide|slides|pptx"
    r"|document[oi]|word|docx"
    r"|fogli[oi]|foglio\s+di\s+calcolo|spreadsheet|excel|xlsx"
    r")\b",
    re.I,
)

# Riferimento esplicito a un file con estensione Office (per il caso "modifica X.pptx").
_FILE_RE = re.compile(r"\b([\w\-.]+\.(pptx|docx|xlsx))\b", re.I)

# Parole chiave → estensione, per inferire il tipo quando non c'è estensione esplicita.
_TYPE_KEYWORDS = [
    (re.compile(r"\b(?:presentazion[ei]|powerpoint|power\s*point|slides?|pptx)\b", re.I), "pptx"),
    (re.compile(r"\b(?:fogli[oi]|foglio\s+di\s+calcolo|spreadsheet|excel|xlsx)\b", re.I), "xlsx"),
    (re.compile(r"\b(?:document[oi]|word|docx)\b", re.I), "docx"),
]

# Directory di output consentita (unica destinazione di scrittura permessa).
_OUTPUT_DIR = Path.home() / "Documents" / "Ari-Output"


# ---------------------------------------------------------------------------
# Prompt di pianificazione per l'LLM
# ---------------------------------------------------------------------------

_PLAN_PROMPT = """Sei un pianificatore che traduce una richiesta in comandi per OfficeCLI, uno strumento a riga di comando per creare documenti Office.

## Sintassi OfficeCLI (comandi principali, verificata sulla documentazione ufficiale)
- `create <file>` — crea un documento vuoto (l'estensione determina il tipo: .pptx, .docx, .xlsx).
- `add <file> <path> --type <tipo> --prop key=value [--prop key2=value2 ...]` — aggiunge un elemento nel punto indicato da <path>.
  - Per una NUOVA slide: path `/`, `--type slide`, `--prop title=...` (il titolo va sulla slide stessa).
  - Per il CONTENUTO testuale di una slide (corpo, elenco punti): NON è una proprietà della slide — va aggiunto come shape SEPARATA con path `/slide[N]` (N = indice della slide, 1-based, nell'ordine in cui è stata aggiunta), `--type shape`, `--prop text="..."` (righe multiple nello stesso testo separate da \\n).
- `set <file> <path> --prop key=value` — imposta una proprietà su un elemento esistente indirizzato da <path> (es. `/slide[1]/shape[1]`).
- `view <file> outline` — mostra la struttura del documento (solo debug, non serve per pianificare).

## Esempio: presentazione con 2 slide
Richiesta: "crea una presentazione su Marte con una slide di titolo e una con 3 punti"
Output:
[
  {{"cmd": "create", "args": ["{output_file}"]}},
  {{"cmd": "add", "args": ["{output_file}", "/", "--type", "slide", "--prop", "title=Marte", "--prop", "subtitle=Il pianeta rosso"]}},
  {{"cmd": "add", "args": ["{output_file}", "/", "--type", "slide", "--prop", "title=Caratteristiche"]}},
  {{"cmd": "add", "args": ["{output_file}", "/slide[2]", "--type", "shape", "--prop", "text=Quarto pianeta dal Sole\\nAtmosfera sottile di CO2\\nDue lune: Phobos e Deimos"]}}
]

## Regole
- Il PRIMO argomento di OGNI comando DEVE essere ESATTAMENTE `{output_file}` — non usare altri path.
- Inizia SEMPRE con un comando `create`.
- Il contenuto testuale (corpo, punti elenco) va SEMPRE aggiunto come shape separata via `--type shape --prop text=...`, mai come proprietà diretta della slide.
- Genera contenuti reali e sensati basati sulla richiesta (non placeholder).
- Rispondi SOLO con l'array JSON, senza testo prima o dopo, senza markdown, senza ```.

## Richiesta dell'utente
{request}

Genera ora l'array JSON di comandi:"""


class OfficeDocsSkill(Skill):
    name        = "office_docs"
    description = "Crea e modifica documenti Office (Word/Excel/PowerPoint) tramite OfficeCLI."
    # need_approval resta False (default): coerente con file_ops (scrive senza
    # approvazione) e la scrittura è confinata a ~/Documents/Ari-Output/.

    # -----------------------------------------------------------------------
    # Trigger
    # -----------------------------------------------------------------------
    def match(self, text: str) -> dict | None:
        if not _TRIGGER_RE.search(text):
            return None

        # 1) Estensione esplicita nel testo ha priorità (caso "modifica X.pptx").
        doc_type = None
        target_name = None
        file_m = _FILE_RE.search(text)
        if file_m:
            target_name = file_m.group(1).strip()
            doc_type = file_m.group(2).lower()

        # 2) Altrimenti inferisci il tipo dalle parole chiave.
        if doc_type is None:
            for pattern, ext in _TYPE_KEYWORDS:
                if pattern.search(text):
                    doc_type = ext
                    break

        if doc_type is None:
            return None

        return {"doc_type": doc_type, "target_name": target_name, "request": text}

    # -----------------------------------------------------------------------
    # Esecuzione
    # -----------------------------------------------------------------------
    async def run(self, user_input: str, params: dict) -> str:
        # 1) Verifica disponibilità del binario (nessuna installazione automatica).
        if shutil.which("officecli") is None:
            return (
                "[OFFICE_DOCS] OfficeCLI non è installato. "
                "Scaricalo da https://github.com/iOfficeAI/OfficeCLI (sezione release) "
                "e assicurati che il binario `officecli` sia nel PATH, poi riprova."
            )

        doc_type    = params.get("doc_type", "pptx")
        target_name = params.get("target_name")
        request     = params.get("request") or user_input

        # 2) Determina il path di output (validato e confinato dalla skill stessa).
        output_path = self._resolve_output_path(target_name, doc_type, request)
        try:
            _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return f"[OFFICE_DOCS] Impossibile creare la directory di output {_OUTPUT_DIR}: {e}"

        # 3) Pianificazione via LLM → sequenza di comandi JSON.
        commands = await self._plan_commands(request, output_path)
        if isinstance(commands, str):
            # _plan_commands ha restituito un messaggio d'errore già formattato.
            return commands

        # 4) Esecuzione della sequenza (in executor, come le altre skill).
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute_commands, commands, output_path
        )

    # -----------------------------------------------------------------------
    # Helper: path di output sicuro
    # -----------------------------------------------------------------------
    def _resolve_output_path(self, target_name: str | None, doc_type: str, request: str) -> Path:
        """Ritorna un path SEMPRE dentro _OUTPUT_DIR, ignorando ogni componente
        di directory fornita dall'utente/LLM (usa solo il nome file)."""
        if target_name:
            stem = Path(target_name).name  # scarta eventuali path assoluti/relativi
        else:
            stem = self._infer_name(request) + f".{doc_type}"

        stem = Path(stem)
        if stem.suffix.lower() not in (".pptx", ".docx", ".xlsx"):
            stem = stem.with_suffix(f".{doc_type}")

        return (_OUTPUT_DIR / stem.name).resolve()

    @staticmethod
    def _infer_name(request: str) -> str:
        """Nome file inferito dalla richiesta: dopo 'su/di/con/riguardo' se c'è,
        altrimenti primi token significativi. Slug prudente [a-z0-9-]."""
        m = re.search(r"\b(?:su|di|riguardo(?:\s+a)?|circa|sul|sulla|sui|sulle)\s+(.+)", request, re.I)
        raw = m.group(1) if m else request
        raw = re.sub(r"\b(?:con|che|per|e|il|la|le|gli|i|un|una|uno)\b.*$", "", raw, flags=re.I)
        slug = re.sub(r"[^\w\s-]", "", raw, flags=re.UNICODE).strip().lower()
        slug = re.sub(r"\s+", "-", slug)[:40].strip("-")
        return slug or "documento"

    def _is_inside_output(self, raw_path: str) -> bool:
        """True se raw_path risolve dentro _OUTPUT_DIR."""
        try:
            resolved = Path(raw_path).expanduser().resolve()
        except Exception:
            return False
        try:
            resolved.relative_to(_OUTPUT_DIR.resolve())
            return True
        except ValueError:
            return False

    # -----------------------------------------------------------------------
    # Helper: pianificazione LLM
    # -----------------------------------------------------------------------
    async def _plan_commands(self, request: str, output_path: Path):
        """Chiede all'LLM la sequenza di comandi. Ritorna una lista di dict, o
        una stringa (messaggio d'errore già formattato) in caso di problema."""
        from ..llm import engine

        prompt = _PLAN_PROMPT.format(output_file=str(output_path), request=request)
        messages = [{"role": "user", "content": prompt}]

        raw = ""
        try:
            async for kind, token in engine.stream(messages, max_tokens=1024, thinking=False):
                if kind == "chunk":
                    raw += token
        except Exception as e:
            log.error(f"errore stream LLM: {e}")
            return f"[OFFICE_DOCS] Errore durante la pianificazione dei comandi: {e}"

        commands = self._parse_json_commands(raw)
        if commands is None:
            log.warning(f"JSON malformato dall'LLM: {raw[:300]!r}")
            return (
                "[OFFICE_DOCS] Non sono riuscita a generare una sequenza di comandi valida "
                "per il documento. Riprova a riformulare la richiesta in modo più semplice."
            )
        if not commands:
            return "[OFFICE_DOCS] La pianificazione non ha prodotto alcun comando."
        return commands

    @staticmethod
    def _parse_json_commands(raw: str):
        """Estrae e valida l'array JSON di comandi. Ritorna una lista di dict
        (ognuno con 'cmd': str, 'args': list[str]) o None se malformato."""
        text = raw.strip()
        # Rimuove eventuali fence markdown.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        # Isola il primo array JSON presente.
        start = text.find("[")
        end   = text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return None
        snippet = text[start:end + 1]

        try:
            data = json.loads(snippet)
        except json.JSONDecodeError:
            return None

        if not isinstance(data, list):
            return None

        commands = []
        for item in data:
            if not isinstance(item, dict):
                return None
            cmd  = item.get("cmd")
            args = item.get("args", [])
            if not isinstance(cmd, str) or not isinstance(args, list):
                return None
            if not all(isinstance(a, str) for a in args):
                return None
            commands.append({"cmd": cmd, "args": args})
        return commands

    # -----------------------------------------------------------------------
    # Helper: esecuzione
    # -----------------------------------------------------------------------
    def _execute_commands(self, commands: list[dict], output_path: Path) -> str:
        for i, cmd in enumerate(commands, start=1):
            name = cmd["cmd"]
            args = cmd["args"]

            # Sicurezza: se il primo argomento è un path di file, DEVE stare
            # dentro _OUTPUT_DIR. Rifiuta e interrompi se punta altrove.
            if args:
                first = args[0]
                looks_like_file = first.lower().endswith((".pptx", ".docx", ".xlsx")) or ("/" in first)
                if looks_like_file and not self._is_inside_output(first):
                    return (
                        f"[OFFICE_DOCS] Comando #{i} ('{name}') rifiutato per sicurezza: "
                        f"tenta di scrivere fuori da {_OUTPUT_DIR} (path: {first}). "
                        "Sequenza interrotta."
                    )

            try:
                proc = subprocess.run(
                    ["officecli", name, *args],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired:
                return f"[OFFICE_DOCS] Comando #{i} ('officecli {name}') scaduto (timeout 30s). Sequenza interrotta."
            except Exception as e:
                return f"[OFFICE_DOCS] Errore eseguendo il comando #{i} ('officecli {name}'): {e}"

            if proc.returncode != 0:
                stderr = (proc.stderr or proc.stdout or "").strip()
                return (
                    f"[OFFICE_DOCS] Comando #{i} fallito: `officecli {name} {' '.join(args)}`\n"
                    f"Codice uscita: {proc.returncode}\n"
                    f"Errore: {stderr or '(nessun output)'}\n"
                    "Sequenza interrotta."
                )

        return (
            f"[OFFICE_DOCS] Documento creato con successo: {output_path}\n"
            f"({len(commands)} comandi eseguiti)"
        )
