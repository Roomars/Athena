"""
MemoryStore v2 — SQLite + BM25 + tags + relations.
Schema esteso compatibile con il vecchio (migrazione automatica).
"""
import math
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"


# ── BM25 minimale (nessuna dipendenza esterna) ────────────────────────────────

def _tokenize(text: str) -> list[str]:
    import re
    return re.split(r"[\s_\-/]+", text.lower())


class _BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        tok = [_tokenize(d) for d in docs]
        self.avgdl = sum(len(d) for d in tok) / max(len(tok), 1)
        self.N  = len(tok)
        self.tf = [Counter(d) for d in tok]
        self.df = Counter(t for doc in tok for t in set(doc))

    def scores(self, query: str) -> list[float]:
        tokens = _tokenize(query)
        out = []
        for i in range(self.N):
            tf = self.tf[i]
            dl = sum(tf.values())
            s  = 0.0
            for t in tokens:
                if t not in tf:
                    continue
                idf = math.log((self.N - self.df[t] + 0.5) / (self.df[t] + 0.5) + 1)
                num = tf[t] * (self.k1 + 1)
                den = tf[t] + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1))
                s  += idf * num / den
            out.append(s)
        return out

    def top_k(self, query: str, k: int = 5) -> list[int]:
        sc = [(i, s) for i, s in enumerate(self.scores(query)) if s > 0]
        sc.sort(key=lambda x: -x[1])
        return [i for i, _ in sc[:k]]


# ── Tags auto-categorizzazione ────────────────────────────────────────────────

_TAG_RULES: dict[str, list[str]] = {
    "identità":    ["nome", "cognome", "soprannome", "età", "nascita"],
    "professione": ["professione", "lavoro", "azienda", "ruolo", "carriera"],
    "tecnologia":  ["progetto", "linguaggio", "framework", "app", "software", "os", "tool"],
    "famiglia":    ["partner", "figli", "genitori", "fratello", "sorella", "famiglia"],
    "interessi":   ["hobby", "sport", "musica", "libro", "film", "gioco", "passione"],
    "posizione":   ["città", "quartiere", "regione", "paese", "indirizzo"],
    "preferenze":  ["preferisce", "piace", "favorito"],
}

def _auto_tags(key: str) -> list[str]:
    kl = key.lower()
    return [tag for tag, kws in _TAG_RULES.items() if any(kw in kl for kw in kws)]


# ── MemoryStore ───────────────────────────────────────────────────────────────

class MemoryStore:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at REAL NOT NULL,
                created_at REAL,
                tags       TEXT DEFAULT '[]',
                confidence REAL DEFAULT 1.0,
                source     TEXT DEFAULT 'extracted'
            );
            CREATE TABLE IF NOT EXISTS relations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                from_key   TEXT NOT NULL,
                to_key     TEXT NOT NULL,
                rel_type   TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS episodes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                summary       TEXT NOT NULL,
                timestamp     REAL NOT NULL,
                message_count INTEGER DEFAULT 0,
                keywords      TEXT DEFAULT '[]'
            );
        """)
        # Migrazione colonne opzionali (ignora se già esistono)
        for col, dflt in [("tags", "'[]'"), ("confidence", "1.0"),
                          ("source", "'extracted'"), ("created_at", "NULL")]:
            try:
                self._db.execute(f"ALTER TABLE facts ADD COLUMN {col} DEFAULT {dflt}")
            except Exception:
                pass
        for col, dflt in [("keywords", "'[]'")]:
            try:
                self._db.execute(f"ALTER TABLE episodes ADD COLUMN {col} DEFAULT {dflt}")
            except Exception:
                pass
        self._db.commit()

    # ── Fatti ─────────────────────────────────────────────────────────────────

    def upsert_fact(self, key: str, value: str,
                    tags: list[str] | None = None,
                    confidence: float = 1.0,
                    source: str = "extracted") -> None:
        key, value = key.strip(), value.strip()
        if not key or not value:
            return
        if tags is None:
            tags = _auto_tags(key)
        now = time.time()
        existing = self._db.execute(
            "SELECT key FROM facts WHERE key = ?", (key,)
        ).fetchone()
        if existing:
            # Supersede relazione: vecchio valore → nuovo
            old_val = self._db.execute(
                "SELECT value FROM facts WHERE key = ?", (key,)
            ).fetchone()["value"]
            if old_val != value:
                self._add_relation(key, key, "Supersedes")
        self._db.execute(
            """INSERT OR REPLACE INTO facts
               (key, value, updated_at, created_at, tags, confidence, source)
               VALUES (?, ?, ?, COALESCE((SELECT created_at FROM facts WHERE key=?), ?), ?, ?, ?)""",
            (key, value, now, key, now, json.dumps(tags), confidence, source),
        )
        self._db.commit()

    def get_facts(self) -> dict[str, str]:
        rows = self._db.execute(
            "SELECT key, value FROM facts ORDER BY updated_at DESC"
        ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def get_facts_full(self) -> list[dict]:
        rows = self._db.execute(
            "SELECT key, value, tags, confidence, updated_at FROM facts ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_fact(self, key: str) -> None:
        self._db.execute("DELETE FROM facts WHERE key = ?", (key,))
        self._db.commit()

    # ── Relazioni ─────────────────────────────────────────────────────────────

    def _add_relation(self, from_key: str, to_key: str, rel_type: str) -> None:
        self._db.execute(
            "INSERT INTO relations (from_key, to_key, rel_type, created_at) VALUES (?,?,?,?)",
            (from_key, to_key, rel_type, time.time()),
        )

    def add_relation(self, from_key: str, to_key: str, rel_type: str) -> None:
        self._add_relation(from_key, to_key, rel_type)
        self._db.commit()

    def get_relations(self) -> list[dict]:
        rows = self._db.execute(
            "SELECT from_key, to_key, rel_type FROM relations ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Episodi ───────────────────────────────────────────────────────────────

    def add_episode(self, summary: str, message_count: int,
                    keywords: list[str] | None = None) -> None:
        self._db.execute(
            "INSERT INTO episodes (summary, timestamp, message_count, keywords) VALUES (?,?,?,?)",
            (summary.strip(), time.time(), message_count, json.dumps(keywords or [])),
        )
        self._db.commit()

    def get_recent_episodes(self, n: int = 5) -> list[dict]:
        rows = self._db.execute(
            "SELECT summary, timestamp, message_count FROM episodes ORDER BY timestamp DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_episodes_full(self, n: int = 50) -> list[dict]:
        rows = self._db.execute(
            "SELECT summary, timestamp, message_count, keywords FROM episodes ORDER BY timestamp DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── BM25 retrieval ────────────────────────────────────────────────────────

    def search_facts(self, query: str, top_k: int = 5) -> list[dict]:
        """BM25 sui fatti: cerca in key + value + tags."""
        rows = self.get_facts_full()
        if not rows:
            return []
        docs = [f"{r['key']} {r['value']} {r.get('tags','')}" for r in rows]
        bm25 = _BM25(docs)
        idxs = bm25.top_k(query, k=top_k)
        return [rows[i] for i in idxs]

    def retrieve_context(self, query: str, top_k: int = 5) -> list[dict]:
        """Multi-query BM25 + RRF — 3 varianti della query."""
        words  = _tokenize(query)
        q2     = " ".join(words[-3:]) if len(words) > 3 else query
        q3     = " ".join(w for w in words if len(w) > 3)

        rows   = self.get_facts_full()
        if not rows:
            return []
        docs   = [f"{r['key']} {r['value']}" for r in rows]
        bm25   = _BM25(docs)

        # RRF fusion (k=60)
        rrf: dict[int, float] = {}
        for q in [query, q2, q3]:
            for rank, idx in enumerate(bm25.top_k(q, k=top_k)):
                rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (60 + rank + 1)

        ranked = sorted(rrf, key=lambda i: -rrf[i])[:top_k]
        return [rows[i] for i in ranked]


memory_store = MemoryStore()
