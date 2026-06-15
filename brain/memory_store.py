import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"


class MemoryStore:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                key        TEXT    PRIMARY KEY,
                value      TEXT    NOT NULL,
                updated_at REAL    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS episodes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                summary       TEXT    NOT NULL,
                timestamp     REAL    NOT NULL,
                message_count INTEGER DEFAULT 0
            );
        """)
        self._db.commit()

    # ── Fatti ────────────────────────────────────────────────────────────────

    def upsert_fact(self, key: str, value: str) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated_at) VALUES (?, ?, ?)",
            (key.strip(), value.strip(), time.time()),
        )
        self._db.commit()

    def get_facts(self) -> dict[str, str]:
        rows = self._db.execute(
            "SELECT key, value FROM facts ORDER BY updated_at DESC"
        ).fetchall()
        return {row["key"]: row["value"] for row in rows}

    def delete_fact(self, key: str) -> None:
        self._db.execute("DELETE FROM facts WHERE key = ?", (key,))
        self._db.commit()

    # ── Episodi ──────────────────────────────────────────────────────────────

    def add_episode(self, summary: str, message_count: int) -> None:
        self._db.execute(
            "INSERT INTO episodes (summary, timestamp, message_count) VALUES (?, ?, ?)",
            (summary.strip(), time.time(), message_count),
        )
        self._db.commit()

    def get_recent_episodes(self, n: int = 5) -> list[dict]:
        rows = self._db.execute(
            "SELECT summary, timestamp FROM episodes ORDER BY timestamp DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(row) for row in rows]


memory_store = MemoryStore()
