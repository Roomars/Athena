import re
from ._base import Skill

_RE = re.compile(
    r"\b(?:"
    r"impara\s+a"
    r"|insegnati\s+(?:a\s+|come\s+)?"
    r"|aggiung[iti]{1,2}\s+(?:la\s+|una\s+)?(?:skill|capacit[àa]|abilit[àa]|funzionalit[àa])"
    r"|crea\s+(?:una?\s+)?(?:nuova?\s+)?(?:skill|abilit[àa]|capacit[àa])"
    r"|costruisciti\s+(?:una?\s+)?(?:skill|tool|funzion|capacit[àa])"
    r"|puoi\s+imparare\s+a"
    r"|fatti\s+(?:una?\s+)?(?:nuova?\s+)?(?:skill|capacit[àa])"
    r"|amplia\s+(?:le\s+)?(?:tue\s+)?capacit[àa]"
    r"|programmati\s+(?:per|a)"
    r"|modifica\s+(?:te\s+stessa|il\s+tuo\s+codice|la\s+tua\s+personalit[àa])"
    r"|aggiorna\s+(?:la\s+)?(?:tua\s+)?personalit[àa]"
    r"|riscriviti\s+la\s+voce"
    r")\b",
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
