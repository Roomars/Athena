"""
Skill: controlla mouse e tastiera via PyAutoGUI con localizzazione VLM-driven.
Pattern UI-TARS: screencapture → Gemma 4 12B trova coordinate → pyautogui agisce.
Trigger: "clicca su X", "premi il tasto X", "digita X", "trova e clicca X".
"""
import re
import logging
from ._base import Skill

log = logging.getLogger("skill.computer_control")

_CTRL_RE = re.compile(
    r'\b(?:clicca\s+(?:su\s+)?(?!safari|il\s+browser)|'
    r'fai\s+(?:un\s+)?(?:clic|click)\s+su\s+|'
    r'premi\s+(?:il\s+)?(?:tasto\s+)?|'
    r'digita\s+|scrivi\s+(?:nella\s+barra|nella\s+casella)|'
    r'trova\s+e\s+clicca|'
    r'doppio\s+clic\s+su)\b',
    re.I,
)

_CLICK_RE   = re.compile(r'\b(?:clicca\s+(?:su\s+)?|fai\s+(?:un\s+)?(?:clic|click)\s+su\s+|trova\s+e\s+clicca\s+(?:su\s+)?)(["\']?)(.+?)\1(?:\s|$|[,.])', re.I)
_DCLICK_RE  = re.compile(r'\b(?:doppio\s+(?:clic|click)\s+(?:su\s+)?)(["\']?)(.+?)\1(?:\s|$|[,.])', re.I)
_TYPE_RE    = re.compile(r'\b(?:digita|scrivi)\s+(?:nella\s+(?:barra|casella)\s+)?["\']?(.+?)["\']?(?:\s|$|[,.])', re.I)
_KEY_RE     = re.compile(r'\bpremi\s+(?:il\s+)?(?:tasto\s+)?["\']?([A-Za-z0-9\+\-\_]+)["\']?(?:\s|$|[,.])', re.I)


class ComputerControlSkill(Skill):
    name          = "computer_control"
    description   = "Controlla mouse e tastiera: clicca elementi trovati via VLM, digita testo, premi tasti."
    need_approval = True

    def match(self, text: str) -> dict | None:
        if not _CTRL_RE.search(text):
            return None

        dclick_m = _DCLICK_RE.search(text)
        if dclick_m:
            return {"action": "double_click", "element": dclick_m.group(2).strip()}

        click_m = _CLICK_RE.search(text)
        if click_m:
            return {"action": "click", "element": click_m.group(2).strip()}

        type_m = _TYPE_RE.search(text)
        if type_m:
            return {"action": "type", "text": type_m.group(1).strip()}

        key_m = _KEY_RE.search(text)
        if key_m:
            return {"action": "key", "key": key_m.group(1).strip()}

        return None

    async def run(self, _user_input: str, params: dict) -> str:
        action = params.get("action", "")

        if action == "type":
            return await _type_text(params.get("text", ""))
        if action == "key":
            return _press_key(params.get("key", ""))

        # click / double_click: usa VLM per trovare le coordinate
        element = params.get("element", "")
        if not element:
            return "[COMPUTER CONTROL] Elemento non specificato."
        return await _vlm_click(element, action)


# ── Azioni dirette (nessuna VLM) ─────────────────────────────────────────────

async def _type_text(text: str) -> str:
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(None, _type_sync, text)


def _type_sync(text: str) -> str:
    try:
        import pyautogui, time
        pyautogui.FAILSAFE = True
        time.sleep(0.2)
        pyautogui.write(text, interval=0.04)
        return f"[COMPUTER CONTROL] Digitato: '{text}'"
    except ImportError:
        return "[COMPUTER CONTROL] PyAutoGUI non installato. Esegui: pip install pyautogui"
    except Exception as e:
        return f"[COMPUTER CONTROL] Errore digitazione: {e}"


def _press_key(key: str) -> str:
    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        # Normalizza nomi tasto comuni
        _MAP = {"invio": "enter", "esc": "escape", "tab": "tab",
                "spazio": "space", "backspace": "backspace", "cancella": "delete",
                "su": "up", "giù": "down", "sinistra": "left", "destra": "right"}
        normalized = _MAP.get(key.lower(), key.lower())
        pyautogui.press(normalized)
        return f"[COMPUTER CONTROL] Tasto premuto: {normalized}"
    except ImportError:
        return "[COMPUTER CONTROL] PyAutoGUI non installato. Esegui: pip install pyautogui"
    except Exception as e:
        return f"[COMPUTER CONTROL] Errore tasto: {e}"


# ── Click VLM-driven ─────────────────────────────────────────────────────────

async def _vlm_click(element: str, action: str) -> str:
    """Cattura screenshot, chiede a Gemma 4 le coordinate, clicca."""
    import asyncio, base64, subprocess, tempfile
    from pathlib import Path

    # 1. Screenshot via screencapture -x (nessun suono, nessuna Swift round-trip)
    tmp = Path(tempfile.mktemp(suffix=".png"))
    r = subprocess.run(["screencapture", "-x", str(tmp)], capture_output=True)
    if r.returncode != 0 or not tmp.exists():
        return "[COMPUTER CONTROL] Impossibile catturare lo schermo (screencapture fallito)."

    b64 = base64.b64encode(tmp.read_bytes()).decode()
    tmp.unlink(missing_ok=True)

    # 2. VLM: trova coordinate
    try:
        from .. import vision
    except ImportError:
        return "[COMPUTER CONTROL] Modulo vision non disponibile."

    prompt = (
        f"Nell'immagine dello schermo, trova l'elemento '{element}'. "
        "Rispondi SOLO con le coordinate pixel del suo centro, nel formato: x,y — "
        "es. 450,320. Se l'elemento non è visibile, scrivi esattamente: non trovato."
    )
    coords_str = await vision.analyze(b64, prompt)
    coords_str = coords_str.strip()
    log.info(f"VLM coords per '{element}': {coords_str!r}")

    if "non trovato" in coords_str.lower():
        return f"[COMPUTER CONTROL] Elemento '{element}' non visibile sullo schermo."

    m = re.search(r'(\d{1,4})[,\s]+(\d{1,4})', coords_str)
    if not m:
        return f"[COMPUTER CONTROL] Coordinate non valide dalla VLM: {coords_str!r}"

    x, y = int(m.group(1)), int(m.group(2))

    # 3. PyAutoGUI click
    return await asyncio.get_event_loop().run_in_executor(None, _click_sync, x, y, action, element)


def _click_sync(x: int, y: int, action: str, element: str) -> str:
    try:
        import pyautogui, time
        pyautogui.FAILSAFE = True
        time.sleep(0.15)
        if action == "double_click":
            pyautogui.doubleClick(x, y)
            return f"[COMPUTER CONTROL] Doppio click su '{element}' ({x},{y})."
        else:
            pyautogui.click(x, y)
            return f"[COMPUTER CONTROL] Click su '{element}' ({x},{y})."
    except ImportError:
        return "[COMPUTER CONTROL] PyAutoGUI non installato. Esegui: pip install pyautogui"
    except pyautogui.FailSafeException:
        return "[COMPUTER CONTROL] FailSafe attivato — mouse nell'angolo superiore sinistro."
    except Exception as e:
        return f"[COMPUTER CONTROL] Errore click: {e}"
