"""
Skill: esegue codice Python o shell in sandbox con timeout.
Trigger: "esegui questo codice", "testa lo script", blocchi ```python/bash.
"""
import re
import logging
from ._base import Skill

log = logging.getLogger("skill.code_runner")

_RUN_RE = re.compile(
    r'\b(?:esegui|testa|lancia|prova|run|eseguire)\s+(?:questo\s+)?(?:codice|script|programma|snippet)\b',
    re.I,
)
_CODE_BLOCK_RE = re.compile(r'```(?P<lang>\w+)?\n(?P<code>[\s\S]+?)```')
_DANGEROUS_RE  = re.compile(
    r'\bsudo\b|rm\s+-rf\s+/|>>\s*/(?:etc|System|private)/|'
    r'curl[^|]+\|\s*(?:sh|bash)|__import__\(["\']os["\']',
    re.I,
)


class CodeRunnerSkill(Skill):
    name        = "code_runner"
    description = "Esegue codice Python o Bash in sandbox con timeout di 30 secondi."

    def match(self, text: str) -> dict | None:
        block_m = _CODE_BLOCK_RE.search(text)
        if block_m and _RUN_RE.search(text):
            return {
                "lang": (block_m.group("lang") or "python").lower(),
                "code": block_m.group("code"),
            }
        return None

    async def run(self, _user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, _execute, params.get("lang", "python"), params.get("code", "")
        )


def _execute(lang: str, code: str) -> str:
    if not code.strip():
        return "[CODE RUNNER] Nessun codice trovato nel messaggio."
    if _DANGEROUS_RE.search(code):
        return "[CODE RUNNER] Bloccato: il codice contiene pattern pericolosi."

    import subprocess, sys, tempfile, os
    timeout = 30
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    try:
        if lang in ("python", "py", "python3"):
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                f.write(code)
                tmp = f.name
            try:
                r = subprocess.run([sys.executable, tmp],
                                   capture_output=True, text=True, timeout=timeout, env=env)
            finally:
                os.unlink(tmp)
        elif lang in ("bash", "shell", "sh"):
            r = subprocess.run(["bash", "-c", code],
                               capture_output=True, text=True, timeout=timeout, env=env)
        else:
            return f"[CODE RUNNER] Linguaggio non supportato: {lang}. Usa python o bash."
    except subprocess.TimeoutExpired:
        return f"[CODE RUNNER] Timeout ({timeout}s) — lo script era troppo lento."

    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if len(out) > 3000:
        out = out[:3000] + f"\n[troncato — totale {len(r.stdout)} chars]"
    if len(err) > 800:
        err = err[:800] + "..."

    lines = [f"[CODE RUNNER: {lang}] exit={r.returncode}"]
    if out:
        lines.append(f"\n{out}")
    if err:
        lines.append(f"\nStderr:\n{err}")
    if not out and not err:
        lines.append("\n(Nessun output)")
    return "\n".join(lines)
