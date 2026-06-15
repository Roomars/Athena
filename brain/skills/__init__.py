from .open_app      import OpenAppSkill
from .web_search    import WebSearchSkill
from .system_info   import SystemInfoSkill
from .clipboard     import ClipboardSkill
from .screen_vision import ScreenVisionSkill

ALL_SKILLS = [
    ScreenVisionSkill(), # prima: pattern specifici, intercettata da ws_handler
    SystemInfoSkill(),
    OpenAppSkill(),
    ClipboardSkill(),
    WebSearchSkill(),    # ultima: "cerca" è termine generico
]
