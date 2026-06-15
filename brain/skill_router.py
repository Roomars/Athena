import logging
from .skills import ALL_SKILLS
from .skills._base import Skill

log = logging.getLogger("skill_router")


class SkillRouter:
    def route(self, text: str) -> tuple[Skill, dict] | None:
        for skill in ALL_SKILLS:
            params = skill.match(text)
            if params is not None:
                log.info(f"skill match: {skill.name} | params={params}")
                return skill, params
        return None


router = SkillRouter()
