"""
MemoryGraph — networkx DiGraph sopra le relazioni SQLite.

Edge types:
  Supersedes   — nuovo valore sostituisce il vecchio (upsert_fact)
  Contradicts  — due fatti si escludono a vicenda (rilevato da LLM async)
  RelatesTo    — associazione semantica
  DerivedFrom  — fatto derivato da un altro (estrazione LLM)
"""
import logging
import time
from typing import Literal

import networkx as nx

log = logging.getLogger("memory_graph")

RelType = Literal["Supersedes", "Contradicts", "RelatesTo", "DerivedFrom"]


class MemoryGraph:
    """
    Wrapper DiGraph su SQLite relations.
    Il grafo è tenuto in memoria e sincronizzato al DB tramite MemoryStore.
    Non possiede la connessione DB — riceve da MemoryStore i dati grezzi.
    """

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    # ── Caricamento ───────────────────────────────────────────────────────────

    def load(self, relations: list[dict]) -> None:
        """Ricostruisce il grafo dalle relazioni SQLite. Chiamato all'avvio."""
        self._g.clear()
        for r in relations:
            self._g.add_edge(
                r["from_key"],
                r["to_key"],
                rel=r["rel_type"],
                t=r.get("created_at", 0),
            )
        log.debug(f"grafo caricato: {self._g.number_of_nodes()} nodi, {self._g.number_of_edges()} archi")

    # ── Aggiornamento ─────────────────────────────────────────────────────────

    def add_edge(self, from_key: str, to_key: str, rel_type: RelType) -> None:
        self._g.add_edge(from_key, to_key, rel=rel_type, t=time.time())

    def remove_node(self, key: str) -> None:
        if self._g.has_node(key):
            self._g.remove_node(key)

    # ── Traversal ─────────────────────────────────────────────────────────────

    def neighbors(self, key: str, rel_filter: RelType | None = None) -> list[str]:
        """Vicini diretti in uscita, opzionalmente filtrati per tipo."""
        if not self._g.has_node(key):
            return []
        out = []
        for _, nbr, data in self._g.out_edges(key, data=True):
            if rel_filter is None or data.get("rel") == rel_filter:
                out.append(nbr)
        return out

    def predecessors(self, key: str, rel_filter: RelType | None = None) -> list[str]:
        """Nodi che puntano a key."""
        if not self._g.has_node(key):
            return []
        out = []
        for pred, _, data in self._g.in_edges(key, data=True):
            if rel_filter is None or data.get("rel") == rel_filter:
                out.append(pred)
        return out

    def cluster(self, key: str, depth: int = 2) -> list[str]:
        """
        Tutti i nodi raggiungibili da key entro `depth` hop (grafo non orientato).
        Utile per espandere il contesto di retrieval.
        """
        if not self._g.has_node(key):
            return []
        undirected = self._g.to_undirected()
        reachable = set()
        frontier = {key}
        for _ in range(depth):
            nxt = set()
            for n in frontier:
                nxt |= set(undirected.neighbors(n))
            frontier = nxt - reachable - {key}
            reachable |= frontier
        return list(reachable)

    def contradicts(self, key: str) -> list[str]:
        """Fatti che contraddicono key."""
        return self.neighbors(key, rel_filter="Contradicts")

    def superseded_by(self, key: str) -> list[str]:
        """Versioni più recenti di key."""
        return self.neighbors(key, rel_filter="Supersedes")

    # ── Ispezione ─────────────────────────────────────────────────────────────

    def node_count(self) -> int:
        return self._g.number_of_nodes()

    def edge_count(self) -> int:
        return self._g.number_of_edges()

    def has_node(self, key: str) -> bool:
        return self._g.has_node(key)

    def to_dict(self) -> dict:
        """Snapshot del grafo per debug/MemoryPanel."""
        return {
            "nodes": list(self._g.nodes()),
            "edges": [
                {"from": u, "to": v, "rel": d.get("rel")}
                for u, v, d in self._g.edges(data=True)
            ],
        }


memory_graph = MemoryGraph()
