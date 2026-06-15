"""
Skill: legge e scrive file locali.
- Leggi: "leggi il file X", "mostrami X", "apri il file X"
- Scrivi: "salva in X", "scrivi nel file X", "crea il file X con..."
- Elenca: "cosa c'è in ~/cartella"
"""
import os
import re
from pathlib import Path
from ._base import Skill

_READ_RE = re.compile(
    r'\b(?:leggi|mostra|apri|visualizza|analizza)\s+(?:il\s+)?file\s+([^\s,]+)',
    re.I,
)
_WRITE_RE = re.compile(
    r'\b(?:salva|scrivi|crea|genera)\s+(?:il\s+)?(?:file\s+|in\s+|nel\s+file\s+)([^\s,]+)',
    re.I,
)
_LIST_RE = re.compile(
    r'\b(?:elenca|lista|cosa\s+c\'è\s+in|contenuto\s+di)\s+([~\w/.]+)',
    re.I,
)

_MAX_SIZE = 8_000   # caratteri massimi per lettura file


class FileOpsSkill(Skill):
    name        = "file_ops"
    description = "Legge e scrive file locali sul Mac."

    def match(self, text: str) -> dict | None:
        m = _READ_RE.search(text)
        if m:
            return {"op": "read", "path": m.group(1)}
        m = _WRITE_RE.search(text)
        if m:
            return {"op": "write", "path": m.group(1)}
        m = _LIST_RE.search(text)
        if m:
            return {"op": "list", "path": m.group(1)}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, params["op"], params["path"], user_input
        )

    def _execute(self, op: str, raw_path: str, user_input: str) -> str:
        path = Path(os.path.expanduser(raw_path)).resolve()

        if op == "read":
            return self._read(path)
        elif op == "list":
            return self._list(path)
        elif op == "write":
            # Il contenuto viene generato dall'LLM — qui restituiamo solo il percorso
            # confermato per l'iniezione nel prompt
            return f"[FILE_WRITE_TARGET: {path}]\nScrivi il contenuto completo da salvare in {path}. " \
                   f"Alla fine della risposta aggiungi la riga esatta: SAVE_TO:{path}"
        return "Operazione non riconosciuta."

    def _read(self, path: Path) -> str:
        if not path.exists():
            return f"File non trovato: {path}"
        if path.stat().st_size > 500_000:
            return f"File troppo grande ({path.stat().st_size // 1024} KB) — usa un editor."
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) > _MAX_SIZE:
                text = text[:_MAX_SIZE] + f"\n\n[... troncato a {_MAX_SIZE} caratteri]"
            return f"[FILE: {path}]\n\n{text}"
        except Exception as e:
            return f"Errore lettura {path}: {e}"

    def _list(self, path: Path) -> str:
        if not path.exists():
            return f"Directory non trovata: {path}"
        if not path.is_dir():
            return f"{path} non è una directory."
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
            lines = [f"{'📁' if e.is_dir() else '📄'} {e.name}" for e in entries[:100]]
            return f"[DIR: {path}]\n" + "\n".join(lines)
        except Exception as e:
            return f"Errore lettura directory {path}: {e}"
