"""
MemoryStore v2 — SQLite + BM25 + TF-IDF cosine + DiGraph + multi-query RRF.
Schema esteso compatibile con il vecchio (migrazione automatica).
"""
import math
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path

try:
    import numpy as _np
    _HAS_NP = True
except ImportError:
    _np = None       # type: ignore[assignment]
    _HAS_NP = False

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

# Import lazy per evitare ciclo (memory_graph importa nulla da qui)
def _graph():
    from .memory_graph import memory_graph
    return memory_graph


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


# ── TF-IDF cosine (dense component, numpy) ───────────────────────────────────

class _TFIDFIndex:
    """
    TF-IDF cosine similarity come componente 'dense'.
    Fallback puro-Python se numpy non disponibile (dot product manuale).
    """

    def __init__(self, docs: list[str]) -> None:
        self._docs = docs
        tok = [_tokenize(d) for d in docs]
        vocab = sorted({t for d in tok for t in d})
        self._vocab = {w: i for i, w in enumerate(vocab)}
        N = len(docs)
        V = len(vocab)

        if _HAS_NP:
            tf_mat = _np.zeros((N, V), dtype=_np.float32)
            for di, tokens in enumerate(tok):
                cnt = Counter(tokens)
                total = max(sum(cnt.values()), 1)
                for w, c in cnt.items():
                    if w in self._vocab:
                        tf_mat[di, self._vocab[w]] = c / total
            df = (_np.array(tf_mat > 0, dtype=_np.float32)).sum(axis=0)
            idf = _np.log((N + 1) / (df + 1)) + 1.0
            self._mat = tf_mat * idf           # (N, V)
            norms = _np.linalg.norm(self._mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._mat /= norms                 # L2-norm per cosine
            self._idf = idf
            self._use_np = True
        else:
            # Fallback: lista di dict tf pesati
            df: Counter = Counter(t for d in tok for t in set(d))
            idf_map = {w: math.log((N + 1) / (df[w] + 1)) + 1.0 for w in vocab}
            self._vecs: list[dict[str, float]] = []
            for tokens in tok:
                cnt = Counter(tokens)
                total = max(sum(cnt.values()), 1)
                vec = {w: (c / total) * idf_map[w] for w, c in cnt.items()}
                norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
                self._vecs.append({w: v / norm for w, v in vec.items()})
            self._idf_map = idf_map
            self._use_np = False

    def _encode_query(self, query: str):
        tokens = _tokenize(query)
        cnt = Counter(tokens)
        total = max(sum(cnt.values()), 1)
        if self._use_np:
            vec = _np.zeros(len(self._vocab), dtype=_np.float32)
            for w, c in cnt.items():
                if w in self._vocab:
                    vec[self._vocab[w]] = (c / total) * self._idf[self._vocab[w]]
            norm = _np.linalg.norm(vec) or 1.0
            return vec / norm
        else:
            vec = {w: (c / total) * self._idf_map.get(w, 0.0) for w, c in cnt.items()}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            return {w: v / norm for w, v in vec.items()}

    def scores(self, query: str) -> list[float]:
        q = self._encode_query(query)
        if self._use_np:
            return (_np.dot(self._mat, q)).tolist()
        else:
            return [sum(q.get(w, 0.0) * v for w, v in doc.items()) for doc in self._vecs]

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
        self._init_graph()

    def _init_graph(self) -> None:
        rows = self._db.execute(
            "SELECT from_key, to_key, rel_type, created_at FROM relations ORDER BY created_at"
        ).fetchall()
        _graph().load([dict(r) for r in rows])

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
        _graph().add_edge(from_key, to_key, rel_type)  # type: ignore[arg-type]

    def add_relation(self, from_key: str, to_key: str, rel_type: str) -> None:
        self._add_relation(from_key, to_key, rel_type)
        self._db.commit()

    def get_cluster(self, key: str, depth: int = 2) -> list[dict]:
        """Restituisce i fatti nel cluster del nodo key (via DiGraph traversal)."""
        keys = _graph().cluster(key, depth=depth)
        if not keys:
            return []
        placeholders = ",".join("?" * len(keys))
        rows = self._db.execute(
            f"SELECT key, value, tags, confidence, updated_at FROM facts WHERE key IN ({placeholders})",
            keys,
        ).fetchall()
        return [dict(r) for r in rows]

    def graph_snapshot(self) -> dict:
        return _graph().to_dict()

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

    # ── Hybrid retrieval: BM25 + TF-IDF cosine + RRF ─────────────────────────

    @staticmethod
    def _rrf_fuse(ranked_lists: list[list[int]], k: int = 60) -> dict[int, float]:
        rrf: dict[int, float] = {}
        for lst in ranked_lists:
            for rank, idx in enumerate(lst):
                rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)
        return rrf

    def search_facts(self, query: str, top_k: int = 5) -> list[dict]:
        """Hybrid BM25+TF-IDF cosine su key+value+tags, RRF fusion."""
        rows = self.get_facts_full()
        if not rows:
            return []
        docs  = [f"{r['key']} {r['value']} {r.get('tags', '')}" for r in rows]
        bm25  = _BM25(docs)
        tfidf = _TFIDFIndex(docs)
        rrf   = self._rrf_fuse([bm25.top_k(query, k=top_k), tfidf.top_k(query, k=top_k)])
        ranked = sorted(rrf, key=lambda i: -rrf[i])[:top_k]
        return [rows[i] for i in ranked]

    def retrieve_context(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Multi-query (5 varianti) × Hybrid (BM25 + TF-IDF cosine) + RRF.
        Espande il recall coprendo varianti lessicali della stessa domanda.
        """
        words = _tokenize(query)
        # 5 varianti della query
        q1 = query
        q2 = " ".join(words[-3:]) if len(words) > 3 else query          # ultimi token
        q3 = " ".join(w for w in words if len(w) > 3)                   # parole sostanziali
        q4 = " ".join(words[:3]) if len(words) > 3 else query           # primi token
        q5 = " ".join(dict.fromkeys(words))                              # deduplicata (ordine)

        rows = self.get_facts_full()
        if not rows:
            return []
        docs  = [f"{r['key']} {r['value']}" for r in rows]
        bm25  = _BM25(docs)
        tfidf = _TFIDFIndex(docs)

        ranked_lists: list[list[int]] = []
        for q in [q1, q2, q3, q4, q5]:
            ranked_lists.append(bm25.top_k(q, k=top_k))
            ranked_lists.append(tfidf.top_k(q, k=top_k))

        rrf    = self._rrf_fuse(ranked_lists)
        ranked = sorted(rrf, key=lambda i: -rrf[i])[:top_k]
        return [rows[i] for i in ranked]


memory_store = MemoryStore()
