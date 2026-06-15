import re
from ._base import Skill

_RE = re.compile(
    r"\b(?:impara\s+a|aggiungi\s+(?:la\s+)?(?:skill|capacit[àa]|abilit[àa]|funzionalit[àa])"
    r"|crea\s+(?:una\s+)?(?:nuova\s+)?skill"
    r"|puoi\s+imparare\s+a|insegnati\s+a"
    r"|modifica\s+(?:te\s+stessa|il\s+tuo\s+codice))\b",
    re.I,
)


class SelfModifySkill(Skill):
    name        = "self_modify"
    description = "Permette ad Ari di aggiungere nuove skill modificando il proprio codice."

    def match(self, text: str) -> dict | None:
        return {} if _RE.search(text) else None

    async def run(self, user_input: str, params: dict) -> str:
        # Intercettata da ws_handler prima di arrivare qui
        return ""
