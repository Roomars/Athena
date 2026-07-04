from .open_app        import OpenAppSkill
from .obsidian        import ObsidianSkill
from .calendar_skill  import CalendarSkill
from .mail_skill      import MailSkill
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
from .flight_finder     import FlightFinderSkill
from .game_updater      import GameUpdaterSkill
from .code_runner       import CodeRunnerSkill
from .browser_control   import BrowserControlSkill
from .computer_control  import ComputerControlSkill

ALL_SKILLS = [
    SelfModifySkill(),       # prima: intercettata da ws_handler
    ScreenVisionSkill(),     # prima di web_fetch per evitare conflitti URL
    ComputerControlSkill(),  # prima di SafariControl (clicca su X)
    SafariControlSkill(),    # URL/navigazione → prima di WebSearch
    BrowserControlSkill(),   # automazione → prima di SafariControl nei trigger specifici
    YoutubeSkill(),          # URL YouTube + ricerca → prima di web_fetch
    WebFetchSkill(),         # URL espliciti → prima di WebSearch
    WeatherSkill(),
    FlightFinderSkill(),
    GameUpdaterSkill(),
    SendMessageSkill(),
    ObsidianSkill(),
    CalendarSkill(),
    MailSkill(),
    ReminderSkill(),
    MacSettingsSkill(),
    DesktopControlSkill(),
    CodeRunnerSkill(),
    FileProcessorSkill(),
    FileOpsSkill(),
    SystemInfoSkill(),
    OpenAppSkill(),
    ClipboardSkill(),
    WebSearchSkill(),        # ultima: "cerca" è termine generico
]
