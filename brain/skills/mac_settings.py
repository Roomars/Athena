"""
Skill: controlla impostazioni di sistema macOS.
Trigger: "alza il volume", "metti dark mode", "blocca schermo", "sleep", ecc.
"""
import re
import subprocess
from ._base import Skill

_RE = re.compile(
    r"(?P<vol_up>alza\s+(?:il\s+)?volume|volume\s+(?:su|pi[uù]\s+alto|alto))"
    r"|(?P<vol_down>abbassa\s+(?:il\s+)?volume|volume\s+(?:gi[uù]|pi[uù]\s+basso|basso))"
    r"|(?P<mute>silenzia|togli\s+(?:l.?audio|il\s+suono)|muta(?:\s+tutto)?|audio\s+off)"
    r"|(?P<unmute>riattiva\s+(?:l.?audio|il\s+suono)|togli\s+il\s+muto|audio\s+on)"
    r"|(?P<vol_set>(?:metti|imposta|porta|setta)\s+(?:il\s+)?volume\s+(?:a\s+|al\s+)?(?P<vol_val>\d{1,3}))"
    r"|(?P<dark>(?:attiva|abilita|metti|passa\s+a(?:lla)?)\s+(?:la\s+)?dark\s+mode|modalit[aà]\s+scura)"
    r"|(?P<light>(?:attiva|abilita|metti|passa\s+a(?:lla)?)\s+(?:la\s+)?(?:light|chiara)\s+mode|modalit[aà]\s+chiara)"
    r"|(?P<sleep>metti\s+(?:il\s+)?(?:mac|computer|schermo)\s+in\s+sleep|sleep\s+mac|vai\s+in\s+sleep)"
    r"|(?P<lock>blocca\s+(?:lo\s+)?schermo|blocca\s+(?:il\s+)?mac)"
    r"|(?P<vol_get>(?:che|a\s+che)\s+(?:volume|livello\s+(?:del\s+)?volume))",
    re.I,
)


def _osascript(script: str) -> tuple[int, str]:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


class MacSettingsSkill(Skill):
    name        = "mac_settings"
    description = "Controlla volume, dark mode, sleep e blocco schermo macOS."

    def match(self, text: str) -> dict | None:
        m = _RE.search(text)
        if not m:
            return None
        groups = {k: v for k, v in m.groupdict().items() if v and k != "vol_val"}
        return {"groups": groups, "vol_val": m.group("vol_val")}

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, params["groups"], params.get("vol_val")
        )

    def _execute(self, groups: dict, vol_val: str | None) -> str:
        if "vol_up" in groups:
            _osascript("set volume output volume (output volume of (get volume settings) + 15)")
            _, v = _osascript("output volume of (get volume settings)")
            return f"[MAC_SETTINGS] Volume alzato ({v}%)."

        if "vol_down" in groups:
            _osascript("set volume output volume (output volume of (get volume settings) - 15)")
            _, v = _osascript("output volume of (get volume settings)")
            return f"[MAC_SETTINGS] Volume abbassato ({v}%)."

        if "mute" in groups:
            _osascript("set volume with output muted")
            return "[MAC_SETTINGS] Audio silenziato."

        if "unmute" in groups:
            _osascript("set volume without output muted")
            return "[MAC_SETTINGS] Audio riattivato."

        if "vol_set" in groups and vol_val:
            v = max(0, min(100, int(vol_val)))
            _osascript(f"set volume output volume {v}")
            return f"[MAC_SETTINGS] Volume impostato a {v}%."

        if "vol_get" in groups:
            _, v = _osascript("output volume of (get volume settings)")
            return f"[MAC_SETTINGS] Volume corrente: {v}%."

        if "dark" in groups:
            _osascript(
                'tell application "System Events" to tell appearance preferences to set dark mode to true'
            )
            return "[MAC_SETTINGS] Dark mode attivata."

        if "light" in groups:
            _osascript(
                'tell application "System Events" to tell appearance preferences to set dark mode to false'
            )
            return "[MAC_SETTINGS] Light mode attivata."

        if "sleep" in groups:
            _osascript('tell application "System Events" to sleep')
            return "[MAC_SETTINGS] Mac in sleep."

        if "lock" in groups:
            subprocess.run(
                ["/System/Library/CoreServices/Menu Extras/User.menu/"
                 "Contents/Resources/CGSession", "-suspend"],
                capture_output=True,
            )
            return "[MAC_SETTINGS] Schermo bloccato."

        return "[MAC_SETTINGS] Azione non riconosciuta."
