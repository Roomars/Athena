"""
Skill: integrazione vault Obsidian.
Trigger: salva/nota/vault, cerca nelle note, cosa ho scritto su X.

Struttura vault:
  AI_Brain/Raw/Inbox/  ← Ari scrive qui (materiale grezzo)
  AI_Brain/Wiki/       ← sola lettura per search
  AI_Brain/Output/     ← output temporanei
"""
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from ._base import Skill

VAULT_ROOT = Path(
    "/Users/roby/Library/CloudStorage/"
    "GoogleDrive-roberto.verzeletti.87@gmail.com/Il mio Drive/AI_Brain"
)
INBOX = VAULT_ROOT / "Raw" / "Inbox"

_DOMAIN_MAP = {
    "Work":       ["cantiere", "impianto", "cliente", "progetto", "lavoro", "offerta", "appalto"],
    "Coach":      ["calcio", "allenamento", "partita", "atleta", "tattica", "u17", "giocatore", "seduta"],
    "MisterLab":  ["misterlab", "mister", "app", "feature", "release", "sprint", "utente"],
    "Developer":  ["codice", "sviluppo", "software", "python", "swift", "bug", "deploy", "programmazione"],
    "AI":         ["intelligenza artificiale", "llm", "modello", "prompt", "agente", "rai", "claude"],
    "Life":       ["personale", "obiettivo", "salute", "abitudine", "routine", "diario"],
    "Social":     ["amico", "networking", "community", "relazione"],
}

_SAVE_RE = re.compile(
    r'\b(?:'
    r'salva\s+(?:questa\s+)?(?:conversazione|nota|risposta|info|informazione)?'
    r'|metti\s+(?:nel\s+)?(?:vault|obsidian|note)'
    r'|nota\s+(?:su|che|questo)'
    r'|annota\s+'
    r'|archivia\s+'
    r'|crea\s+(?:una\s+)?nota\s+(?:su\s+)?'
    r'|aggiungi\s+(?:a|in)\s+(?:vault|obsidian)'
    r')',
    re.I,
)
_SEARCH_RE = re.compile(
    r'\b(?:'
    r'cerca\s+(?:nelle\s+)?note\s+(?:su\s+)?'
    r'|cosa\s+ho\s+scritto\s+su\s+'
    r'|trova\s+(?:nota|note)\s+(?:su\s+)?'
    r'|ho\s+scritto\s+qualcosa\s+su\s+'
    r'|cerca\s+in\s+obsidian\s+'
    r'|cerca\s+nel\s+vault\s+'
    r')',
    re.I,
)


def _detect_domain(text: str) -> str:
    low = text.lower()
    scores = {d: sum(1 for kw in kws if kw in low) for d, kws in _DOMAIN_MAP.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Varius"


def _search_vault(query: str, max_results: int = 5) -> list[dict]:
    """Cerca full-text in tutti i .md del vault. Ritorna lista {path, score, excerpt}."""
    terms = [t.lower() for t in query.split() if len(t) > 2]
    if not terms:
        return []

    results = []
    for md in VAULT_ROOT.rglob("*.md"):
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        low = content.lower()
        score = sum(low.count(t) for t in terms)
        if score == 0:
            continue
        # Trova excerpt: prima occorrenza del primo termine
        pos = low.find(terms[0])
        start = max(0, pos - 60)
        end   = min(len(content), pos + 200)
        excerpt = content[start:end].replace("\n", " ").strip()
        rel = str(md.relative_to(VAULT_ROOT))
        results.append({"path": rel, "score": score, "excerpt": excerpt, "name": md.stem})

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


def _save_note(title: str, body: str, domain: str | None = None) -> str:
    """Salva nota in Raw/Inbox/ con frontmatter YAML."""
    INBOX.mkdir(parents=True, exist_ok=True)
    now    = datetime.now()
    slug   = re.sub(r"[^\w\-]", "_", title[:40].strip())
    fname  = f"{now.strftime('%Y-%m-%d_%H-%M')}_{slug}.md"
    dom    = domain or _detect_domain(title + " " + body)
    tags   = ["ari", dom.lower()]

    frontmatter = (
        f"---\n"
        f"date: {now.strftime('%Y-%m-%d')}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"source: ari\n"
        f"domain: {dom}\n"
        f"---\n\n"
    )
    content = frontmatter + f"# {title}\n\n{body}\n"
    path = INBOX / fname
    path.write_text(content, encoding="utf-8")
    return str(path.relative_to(VAULT_ROOT))


class ObsidianSkill(Skill):
    name        = "obsidian"
    description = "Leggi e scrivi note nel vault Obsidian locale."

    def match(self, text: str) -> dict | None:
        if _SEARCH_RE.search(text):
            query = _SEARCH_RE.sub("", text).strip().rstrip("?.,!")
            return {"action": "search", "query": query or text}
        if _SAVE_RE.search(text):
            title = _SAVE_RE.sub("", text).strip().rstrip("?.,!") or "Nota Ari"
            return {"action": "save", "title": title, "body": ""}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, user_input, params
        )

    def _execute(self, user_input: str, params: dict) -> str:
        action = params.get("action")

        if action == "search":
            query = params.get("query", user_input)
            results = _search_vault(query)
            if not results:
                return f"[OBSIDIAN] Nessuna nota trovata per: «{query}»"
            lines = [f"[OBSIDIAN] {len(results)} note trovate per «{query}»:"]
            for r in results:
                lines.append(f"\n📄 {r['name']} ({r['path']})\n   {r['excerpt'][:180]}…")
            return "\n".join(lines)

        if action == "save":
            title = params.get("title") or user_input[:60]
            body  = params.get("body") or user_input
            rel   = _save_note(title, body)
            return f"[OBSIDIAN] Nota salvata in Raw/Inbox/: {rel}"

        return "[OBSIDIAN] Azione non riconosciuta."


# Esportato per uso diretto da ws_handler / heartbeat
def save_note(title: str, body: str, domain: str | None = None) -> str:
    return _save_note(title, body, domain)

def search_vault(query: str, max_results: int = 5) -> list[dict]:
    return _search_vault(query, max_results)
