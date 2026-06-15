"""
Skill: recupera e legge il contenuto testuale di un URL.
Trigger: URL esplicito nel testo, oppure "analizza sito/pagina", "leggi sito", ecc.
"""
import re
from ._base import Skill

_URL_RE = re.compile(r'https?://[^\s\'"<>]+', re.I)

_CMD_RE = re.compile(
    r'\b(?:analizza|leggi|apri|visita|vai\s+su|controlla|esamina|cosa\s+dice|'
    r'informazioni\s+su|notizie\s+da)\b.{0,60}https?://',
    re.I | re.S,
)


class WebFetchSkill(Skill):
    name        = "web_fetch"
    description = "Recupera e analizza il contenuto testuale di un URL."

    def match(self, text: str) -> dict | None:
        url_m = _URL_RE.search(text)
        if url_m:
            return {"url": url_m.group(0).rstrip(".,;:)")}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._fetch, params["url"])

    def _fetch(self, url: str) -> str:
        try:
            import httpx
            from bs4 import BeautifulSoup

            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                     "AppleWebKit/537.36 Chrome/120 Safari/537.36"}
            resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Rimuovi script, style, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Comprimi righe vuote multiple
            text = re.sub(r'\n{3,}', '\n\n', text).strip()

            # Tronca a ~4000 caratteri per non esplodere il contesto
            if len(text) > 4000:
                text = text[:4000] + f"\n\n[... testo troncato a 4000 caratteri su {len(text)} totali]"

            return f"[URL: {url}]\n\n{text}"

        except Exception as e:
            return f"Errore nel recupero di {url}: {e}"
