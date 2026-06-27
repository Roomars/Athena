from datetime import datetime
from pathlib import Path

from .memory_store import memory_store

_CONST_DIR = Path(__file__).parent.parent / "constitution"


def build_system_prompt(query: str = "") -> str:
    def _read(name: str) -> str:
        p = _CONST_DIR / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    ari  = _read("ari.md")
    roby = _read("roby.md")
    now  = datetime.now().strftime("%A %d %B %Y, %H:%M")

    base = f"""{ari}

---

{roby}

---

Data e ora corrente: {now}""".strip()

    sections: list[str] = []

    # Retrieval contestuale: top-5 fatti rilevanti per la query corrente.
    # Se non c'è query (es. system prompt statico), carica tutti i fatti.
    if query:
        facts = memory_store.retrieve_context(query, top_k=5)
        if facts:
            lines = "\n".join(f"- {r['key']}: {r['value']}" for r in facts)
            sections.append(f"## Quello che ricordo dell'utente (rilevante)\n{lines}")
    else:
        flat = memory_store.get_facts()
        if flat:
            lines = "\n".join(f"- {k}: {v}" for k, v in flat.items())
            sections.append(f"## Quello che ricordo dell'utente\n{lines}")

    episodes = memory_store.get_recent_episodes(3)
    if episodes:
        lines = "\n".join(f"- {ep['summary']}" for ep in episodes)
        sections.append(f"## Sessioni recenti\n{lines}")

    if sections:
        base += "\n\n---\n\n" + "\n\n".join(sections)

    return base
