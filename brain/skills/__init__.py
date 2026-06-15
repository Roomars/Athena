from .open_app          import OpenAppSkill
from .web_search        import WebSearchSkill
from .web_fetch         import WebFetchSkill
from .system_info       import SystemInfoSkill
from .clipboard         import ClipboardSkill
from .file_ops          import FileOpsSkill
from .screen_vision     import ScreenVisionSkill
from .self_modify_skill import SelfModifySkill

ALL_SKILLS = [
    SelfModifySkill(),   # prima: intercettata da ws_handler, guardrail esplicito
    ScreenVisionSkill(),
    WebFetchSkill(),     # URL espliciti — match prima di WebSearch
    FileOpsSkill(),
    SystemInfoSkill(),
    OpenAppSkill(),
    ClipboardSkill(),
    WebSearchSkill(),    # ultima: "cerca" è termine generico
]
