import asyncio
import json
import re
import urllib.parse
import urllib.request

from ._base import Skill

_RE = re.compile(
    r"\b(?:cerca|ricerca|trova|cerca online|cerca su google|cerca su internet|ddg|googla)\s+(.+)",
    re.I,
)

_DDG_URL = "https://api.duckduckgo.com/?format=json&no_html=1&skip_disambig=1&q={q}"


def _fetch(query: str) -> str:
    url = _DDG_URL.format(q=urllib.parse.quote(query))
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return f"[SKILL web_search] Errore connessione: {e}"

    parts: list[str] = []
    if data.get("Answer"):
        parts.append(data["Answer"])
    if data.get("AbstractText"):
        parts.append(data["AbstractText"])
    for topic in data.get("RelatedTopics", [])[:3]:
        if isinstance(topic, dict) and topic.get("Text"):
            parts.append(topic["Text"])

    if parts:
        combined = " | ".join(parts[:4])
        return f"[SKILL web_search] Risultati per '{query}': {combined}"
    return (
        f"[SKILL web_search] Nessun risultato istantaneo per '{query}'. "
        "Suggerisci all'utente di aprire un browser per approfondire."
    )


class WebSearchSkill(Skill):
    name = "web_search"
    description = "Cerca su DuckDuckGo e restituisce risposte istantanee."

    def match(self, text: str) -> dict | None:
        m = _RE.search(text)
        return {"query": m.group(1).strip()} if m else None

    async def run(self, user_input: str, params: dict) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch, params["query"])
