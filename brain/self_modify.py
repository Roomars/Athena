"""
Motore di auto-modifica — lettura file, diff, scrittura, git commit, restart.
Opera SOLO su brain/ — mai su Swift, mai su file di sistema.
"""
import difflib
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path

log = logging.getLogger("self_modify")

BRAIN_ROOT  = Path(__file__).parent
REPO_ROOT   = BRAIN_ROOT.parent
SWIFT_ROOT  = REPO_ROOT / "AriApp" / "Sources" / "AriApp"
CONST_ROOT  = REPO_ROOT / "constitution"


def read_file(rel_path: str) -> str:
    return (BRAIN_ROOT / rel_path).read_text(encoding="utf-8")


def file_exists(rel_path: str) -> bool:
    return (BRAIN_ROOT / rel_path).exists()


def list_python_files() -> list[str]:
    return sorted(
        str(p.relative_to(BRAIN_ROOT))
        for p in BRAIN_ROOT.rglob("*.py")
        if "__pycache__" not in str(p)
    )


def compute_diff(original: str, modified: str, filename: str) -> str:
    orig_lines = original.splitlines(keepends=True)
    new_lines  = modified.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        orig_lines, new_lines,
        fromfile=f"a/{filename}", tofile=f"b/{filename}",
        lineterm="",
    ))
    return "\n".join(diff)


# ── Percorsi per scope ───────────────────────────────────────────────────────

def _resolve(scope: str, rel_path: str) -> Path:
    """Ritorna il Path assoluto dato scope (brain|swift|constitution) e percorso relativo."""
    if scope == "brain":
        return BRAIN_ROOT / rel_path
    elif scope == "swift":
        return SWIFT_ROOT / rel_path
    elif scope == "constitution":
        return CONST_ROOT / rel_path
    else:
        raise ValueError(f"Scope non valido: {scope}")


def read_scoped(scope: str, rel_path: str) -> str:
    return _resolve(scope, rel_path).read_text(encoding="utf-8")


def file_exists_scoped(scope: str, rel_path: str) -> bool:
    return _resolve(scope, rel_path).exists()


def list_swift_files() -> list[str]:
    return sorted(
        str(p.relative_to(SWIFT_ROOT))
        for p in SWIFT_ROOT.rglob("*.swift")
        if "__pycache__" not in str(p)
    )


# ── Apply con backup per rollback ─────────────────────────────────────────────

def apply_changes(changes: list[dict]) -> dict[str, str]:
    """
    Scrive i file. Ogni change: {scope: str, rel_path: str, content: str}
    Ritorna backup {key → original_content} per rollback.
    """
    backups: dict[str, str] = {}
    for change in changes:
        path = _resolve(change["scope"], change["rel_path"])
        key  = f"{change['scope']}:{change['rel_path']}"
        backups[key] = path.read_text(encoding="utf-8") if path.exists() else ""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(change["content"], encoding="utf-8")
        log.info(f"Scritto [{change['scope']}]: {path}")
    return backups


def rollback(backups: dict[str, str]) -> None:
    """Ripristina i file originali dai backup."""
    for key, content in backups.items():
        scope, rel_path = key.split(":", 1)
        path = _resolve(scope, rel_path)
        if content:
            path.write_text(content, encoding="utf-8")
            log.info(f"Rollback [{scope}]: {path}")
        elif path.exists():
            path.unlink()
            log.info(f"Rollback (rimosso) [{scope}]: {path}")


# ── Vecchia firma mantenuta per compatibilità con skill Python ────────────────

def apply_brain_changes(changes: list[dict]) -> dict[str, str]:
    """Scrive solo file brain/. changes: [{rel_path, content}]"""
    scoped = [{"scope": "brain", **c} for c in changes]
    return apply_changes(scoped)


def git_commit(message: str, changes: list[dict] | None = None) -> str:
    scopes = {c["scope"] for c in changes} if changes else {"brain"}
    paths  = []
    if "brain"        in scopes: paths.append("brain/")
    if "swift"        in scopes: paths.append("AriApp/")
    if "constitution" in scopes: paths.append("constitution/")
    for p in paths:
        subprocess.run(["git", "add", p], cwd=REPO_ROOT, capture_output=True)
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    out = result.stdout.strip()
    log.info(f"git commit: {out}")
    return out


def restart_daemon(delay: float = 1.5) -> None:
    """Esce dopo 'delay' secondi — DaemonManager in Swift rilancerà il processo."""
    def _exit():
        time.sleep(delay)
        log.info("Self-restart: uscita per riavvio daemon.")
        sys.exit(0)
    threading.Thread(target=_exit, daemon=True).start()
