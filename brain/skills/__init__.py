from .open_app         import OpenAppSkill
from .web_search       import WebSearchSkill
from .system_info      import SystemInfoSkill
from .clipboard        import ClipboardSkill
from .screen_vision    import ScreenVisionSkill
from .self_modify_skill import SelfModifySkill

ALL_SKILLS = [
    SelfModifySkill(),   # prima: intercettata da ws_handler, guardrail esplicito
    ScreenVisionSkill(),
    SystemInfoSkill(),
    OpenAppSkill(),
    ClipboardSkill(),
    WebSearchSkill(),    # ultima: "cerca" è termine generico
]
