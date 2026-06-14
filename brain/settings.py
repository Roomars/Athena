import json
import logging
from pathlib import Path

SETTINGS_DIR = Path.home() / "Library" / "Application Support" / "Ari"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

DEFAULTS = {
    "version": 1,
    "hotkey": "cmd+shift+a",
    "wake_word_enabled": False,
    "orb_position": "notch",
    "silent_mode_schedule": {"enabled": False, "from": "23:00", "to": "07:00"},
    "vault_input_path": str(Path.home() / "Library/CloudStorage/GoogleDrive/AthenaInput"),
    "vault_local_path": str(Path.home() / ".ari/vault"),
    "llm_primary": "qwen3:14b",
    "llm_heavy": "qwen2.5:32b",
    "nvidia_fallback_enabled": False,
    "tts_voice": "Federica (Premium)",
    "home_assistant": {"url": "", "token": ""},
    "setup_completed": False,
}

log = logging.getLogger("settings")
_cache: dict = {}


def load() -> dict:
    global _cache
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        save(DEFAULTS.copy())
        log.info("settings.json creato con valori default")
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        _cache = json.load(f)
    return _cache


def save(data: dict):
    global _cache
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _cache = data


def get(key: str, default=None):
    return _cache.get(key, default)
