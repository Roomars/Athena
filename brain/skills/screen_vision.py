import re
from ._base import Skill

_RE = re.compile(
    r"\b(?:descrivi\s+(?:lo\s+)?schermo|cosa\s+(?:c[''`]è|vedi|hai)\s+(?:sullo\s+)?schermo"
    r"|guarda\s+(?:lo\s+)?schermo|analizza\s+(?:lo\s+)?schermo"
    r"|cosa\s+sta\s+succedendo\s+(?:sullo\s+)?schermo"
    r"|quante?\s+(?:finestre|app|applicazioni|programmi)"
    r"|(?:c[''`]è|ci\s+sono)\s+(?:qualcosa|qualche)\s+(?:di\s+)?(?:anomal|stran|insolito)"
    r"|anomali[ae]\s+(?:sullo\s+)?schermo"
    r"|zona\s+(?:attiva|con\s+più\s+attività)"
    r"|screenshot|screen|schermata)\b",
    re.I,
)


class ScreenVisionSkill(Skill):
    name        = "screen_vision"
    description = "Analizza il contenuto dello schermo tramite visione strutturata."

    def match(self, text: str) -> dict | None:
        return {} if _RE.search(text) else None

    async def run(self, _user_input: str, _params: dict) -> str:
        # Non usata direttamente — ws_handler intercetta questa skill prima dell'LLM
        return ""
