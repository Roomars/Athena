from abc import ABC, abstractmethod


class Skill(ABC):
    name: str
    description: str
    # Se True, ws_handler chiede approvazione a Swift prima di eseguire.
    # Applicabile a skill pericolose: computer_control, code_runner.
    need_approval: bool = False

    @abstractmethod
    def match(self, text: str) -> dict | None:
        """Ritorna un dict di parametri se il testo attiva la skill, None altrimenti."""

    @abstractmethod
    async def run(self, user_input: str, params: dict) -> str:
        """Esegue la skill e ritorna una stringa di contesto da iniettare nell'LLM."""
