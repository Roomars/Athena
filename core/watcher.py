import threading
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from core.brain import VAULT_PATH, SKIP_DIRS, index_file, remove_file


class _VaultHandler(FileSystemEventHandler):
    def _should_process(self, path: str) -> bool:
        p = Path(path)
        if p.suffix != ".md":
            return False
        return not any(skip in p.parts for skip in SKIP_DIRS)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._should_process(event.src_path):
            index_file(Path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._should_process(event.src_path):
            index_file(Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._should_process(event.src_path):
            remove_file(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            if self._should_process(event.src_path):
                remove_file(Path(event.src_path))
            if self._should_process(event.dest_path):
                index_file(Path(event.dest_path))


_observer: Optional[Observer] = None


def start(vault_path: Path = VAULT_PATH) -> None:
    global _observer
    if _observer is not None:
        return
    if not vault_path.exists():
        return

    _observer = Observer()
    _observer.schedule(_VaultHandler(), str(vault_path), recursive=True)
    t = threading.Thread(target=_observer.start, daemon=True)
    t.start()


def stop() -> None:
    global _observer
    if _observer:
        _observer.stop()
        _observer.join()
        _observer = None
