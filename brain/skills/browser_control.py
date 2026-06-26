"""
Skill: automazione browser via Playwright (Chromium headed).
Trigger: "automatizza X", "compila il form su X", "clicca il bottone X su Y",
         "estrai dati da X", "apri il browser e fai X".
Differenza da safari_control: supporta click, form fill, estrazione dati.
"""
import re
import logging
from ._base import Skill

log = logging.getLogger("skill.browser_control")

_BROWSER_RE = re.compile(
    r'\b(?:automatizza|compila\s+(?:il\s+)?form|'
    r'clicca\s+(?:il\s+)?(?:bottone|pulsante|link|button)|'
    r'estrai\s+(?:i\s+)?dati\s+da|scrivi\s+nel\s+campo|'
    r'apri\s+il\s+browser|'
    r'(?:vai\s+su|apri)\s+.+\s+e\s+(?:clicca|compila|cerca|scrivi))\b',
    re.I,
)

_URL_RE     = re.compile(r'https?://[^\s]+|(?:www\.)?[\w\-]+\.[a-z]{2,}[^\s]*', re.I)
_CLICK_RE   = re.compile(r'\bclicca\s+(?:su\s+)?["\']?([^"\',.!?\n]{2,40})["\']?', re.I)
_FILL_RE    = re.compile(r'\bscrivi\s+["\']?([^"\']+)["\']?\s+nel\s+campo\s+["\']?([^"\',.!\n]+)["\']?', re.I)
_SEARCH_RE  = re.compile(r'\bcerca\s+["\']?([^"\',.!\n]{2,60})["\']?', re.I)
_EXTRACT_RE = re.compile(r'\b(?:estrai|leggi|prendi)\s+(?:i\s+)?(?:dati|testo|contenuto|prezzi|titoli)\b', re.I)


def _parse_actions(text: str) -> list[dict]:
    actions = []
    url_m = _URL_RE.search(text)
    if url_m:
        raw = url_m.group(0).rstrip(".,;)")
        url = raw if raw.startswith("http") else "https://" + raw
        actions.append({"type": "navigate", "url": url})

    fill_m = _FILL_RE.search(text)
    if fill_m:
        actions.append({"type": "fill", "value": fill_m.group(1).strip(),
                        "label": fill_m.group(2).strip()})

    search_m = _SEARCH_RE.search(text)
    if search_m and not fill_m:
        actions.append({"type": "search", "query": search_m.group(1).strip()})

    click_m = _CLICK_RE.search(text)
    if click_m:
        actions.append({"type": "click", "text": click_m.group(1).strip()})

    if _EXTRACT_RE.search(text):
        actions.append({"type": "extract"})

    if not actions:
        actions.append({"type": "extract"})

    return actions


class BrowserControlSkill(Skill):
    name        = "browser_control"
    description = "Automatizza il browser (Chromium) via Playwright: naviga, clicca, compila form, estrae dati."

    def match(self, text: str) -> dict | None:
        if not _BROWSER_RE.search(text):
            return None
        return {"actions": _parse_actions(text)}

    async def run(self, _user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, _run_browser, params.get("actions", [])
        )


def _run_browser(actions: list[dict]) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return (
            "[BROWSER CONTROL] Playwright non installato.\n"
            "Esegui: pip install playwright && playwright install chromium"
        )

    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page    = browser.new_page()
            page.set_default_timeout(10_000)

            for action in actions:
                t = action["type"]
                try:
                    if t == "navigate":
                        page.goto(action["url"], wait_until="domcontentloaded")
                        results.append(f"Navigato su: {page.url}")

                    elif t == "search":
                        # Prova input[type=search] → input[name*=q] → primo input testo
                        for sel in ('input[type="search"]', 'input[name*="q"]',
                                    'input[name*="search"]', 'input[type="text"]'):
                            try:
                                page.fill(sel, action["query"])
                                page.keyboard.press("Enter")
                                page.wait_for_load_state("domcontentloaded")
                                results.append(f"Cercato: {action['query']!r}")
                                break
                            except Exception:
                                continue

                    elif t == "fill":
                        label = action["label"]
                        for sel in (
                            f'input[placeholder*="{label}"]',
                            f'input[name*="{label}"]',
                            f'label:has-text("{label}") input',
                            f'[aria-label*="{label}"]',
                        ):
                            try:
                                page.fill(sel, action["value"])
                                results.append(f"Campo '{label}' compilato con '{action['value']}'")
                                break
                            except Exception:
                                continue

                    elif t == "click":
                        clicked = False
                        for sel in (
                            f'text="{action["text"]}"',
                            f'button:has-text("{action["text"]}")',
                            f'a:has-text("{action["text"]}")',
                            f'[aria-label*="{action["text"]}"]',
                        ):
                            try:
                                page.click(sel, timeout=4000)
                                page.wait_for_load_state("domcontentloaded", timeout=5000)
                                results.append(f"Cliccato: {action['text']!r}")
                                clicked = True
                                break
                            except Exception:
                                continue
                        if not clicked:
                            results.append(f"Elemento '{action['text']}' non trovato.")

                    elif t == "extract":
                        title = page.title()
                        # Rimuovi script/style e prendi il testo principale
                        page.evaluate("document.querySelectorAll('script,style,nav,footer').forEach(e=>e.remove())")
                        text = page.inner_text("body").strip()
                        text = re.sub(r'\n{3,}', '\n\n', text)
                        if len(text) > 3000:
                            text = text[:3000] + "\n[troncato]"
                        results.append(f"Pagina: {title}\n\n{text}")

                except Exception as e:
                    results.append(f"Errore azione '{t}': {e}")

            browser.close()

    except Exception as e:
        return f"[BROWSER CONTROL] Errore Playwright: {e}"

    return "[BROWSER CONTROL]\n\n" + "\n\n".join(results)
