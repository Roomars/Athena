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

BRAIN_ROOT = Path(__file__).parent
REPO_ROOT  = BRAIN_ROOT.parent


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


def apply_changes(changes: list[dict]) -> None:
    """Scrive i file. Ogni change: {rel_path: str, content: str}"""
    for change in changes:
        path = BRAIN_ROOT / change["rel_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(change["content"], encoding="utf-8")
        log.info(f"Scritto: {path}")


def git_commit(message: str) -> str:
    subprocess.run(["git", "add", "brain/"], cwd=REPO_ROOT, capture_output=True)
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
