import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path.home() / "Library" / "Logs" / "Ari"
LOG_FILE = LOG_DIR / "ari.log"

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler_file = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler_file.setFormatter(fmt)

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler_file)
    root.addHandler(handler_console)

    # Silenzia logger verbosi di librerie terze
    for noisy in ("httpx", "httpcore", "huggingface_hub", "filelock"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
