from .open_app        import OpenAppSkill
from .safari_control  import SafariControlSkill
from .web_search      import WebSearchSkill
from .youtube         import YoutubeSkill
from .web_fetch       import WebFetchSkill
from .weather         import WeatherSkill
from .send_message    import SendMessageSkill
from .reminder        import ReminderSkill
from .mac_settings    import MacSettingsSkill
from .desktop_control import DesktopControlSkill
from .system_info     import SystemInfoSkill
from .clipboard       import ClipboardSkill
from .file_processor  import FileProcessorSkill
from .file_ops        import FileOpsSkill
from .screen_vision   import ScreenVisionSkill
from .self_modify_skill import SelfModifySkill

ALL_SKILLS = [
    SelfModifySkill(),    # prima: intercettata da ws_handler
    ScreenVisionSkill(),  # prima di web_fetch per evitare conflitti URL
    SafariControlSkill(), # URL/navigazione → prima di WebSearch
    YoutubeSkill(),       # URL YouTube + ricerca → prima di web_fetch
    WebFetchSkill(),      # URL espliciti → prima di WebSearch
    WeatherSkill(),
    SendMessageSkill(),
    ReminderSkill(),
    MacSettingsSkill(),
    DesktopControlSkill(),
    FileProcessorSkill(),
    FileOpsSkill(),
    SystemInfoSkill(),
    OpenAppSkill(),
    ClipboardSkill(),
    WebSearchSkill(),     # ultima: "cerca" è termine generico
]
