"""
SparkStore — SQLite persistence per spark proattivi.

Ogni notifica proattiva inviata viene registrata con trigger_id,
timestamp, titolo e corpo. Permette rate limiting e cooldown
persistenti tra riavvii, a differenza degli in-memory dict.
"""
import sqlite3
import time
import threading
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".ari" / "sparks.db"


class SparkStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn  = sqlite3.connect(str(db_path), check_same_thread=False)
        self._lock  = threading.Lock()
        self._create_table()

    def _create_table(self) -> None:
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS sparks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_id  TEXT    NOT NULL,
                    title       TEXT,
                    body        TEXT,
                    fired_at    REAL    NOT NULL
                )
            """)
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trigger_fired "
                "ON sparks(trigger_id, fired_at)"
            )
            self._conn.commit()

    def record(self, trigger_id: str, title: str, body: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO sparks(trigger_id, title, body, fired_at) VALUES (?,?,?,?)",
                (trigger_id, title, body, time.time()),
            )
            self._conn.commit()

    def cooldown_ok(self, trigger_id: str, cooldown_hours: float) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "SELECT MAX(fired_at) FROM sparks WHERE trigger_id=?",
                (trigger_id,),
            )
            last = cur.fetchone()[0] or 0.0
        return (time.time() - last) >= cooldown_hours * 3600

    def count_today(self, trigger_id: str) -> int:
        today_start = _today_ts()
        with self._lock:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM sparks WHERE trigger_id=? AND fired_at>=?",
                (trigger_id, today_start),
            )
            return cur.fetchone()[0]

    def total_today(self) -> int:
        today_start = _today_ts()
        with self._lock:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM sparks WHERE fired_at>=?",
                (today_start,),
            )
            return cur.fetchone()[0]

    def recent(self, limit: int = 20) -> list[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT trigger_id, title, body, fired_at "
                "FROM sparks ORDER BY fired_at DESC LIMIT ?",
                (limit,),
            )
            return [
                {"trigger_id": r[0], "title": r[1], "body": r[2], "fired_at": r[3]}
                for r in cur.fetchall()
            ]


def _today_ts() -> float:
    now = datetime.now()
    return datetime(now.year, now.month, now.day).timestamp()


spark_store = SparkStore()
