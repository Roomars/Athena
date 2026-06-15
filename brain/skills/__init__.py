from .open_app   import OpenAppSkill
from .web_search import WebSearchSkill
from .system_info import SystemInfoSkill
from .clipboard  import ClipboardSkill

ALL_SKILLS = [
    SystemInfoSkill(),   # priorità alta: pattern specifici, rischio basso
    OpenAppSkill(),
    ClipboardSkill(),
    WebSearchSkill(),    # ultima: "cerca" è termine generico
]
