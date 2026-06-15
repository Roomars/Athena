from .system_triggers import BatteryTrigger, CPUTrigger, MemoryTrigger
from .time_triggers   import MorningGreetingTrigger, EveningCheckInTrigger

ALL_TRIGGERS = [
    BatteryTrigger(),
    CPUTrigger(),
    MemoryTrigger(),
    MorningGreetingTrigger(),
    EveningCheckInTrigger(),
]
