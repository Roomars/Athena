"""
Skill: controlla il desktop macOS (sfondo, Dock, Finder, Cestino).
Trigger: "cambia sfondo", "nascondi dock", "svuota cestino", ecc.
"""
import re
import subprocess
from ._base import Skill

_RE = re.compile(
    r'\b(?:'
    r'(?P<dock_hide>nascondi\s+(?:il\s+)?dock|dock\s+off|dock\s+automatico)'
    r'|(?P<dock_show>mostra\s+(?:il\s+)?dock|dock\s+on|dock\s+fisso)'
    r'|(?P<trash_empty>svuota\s+(?:il\s+)?cestino|pulisci\s+(?:il\s+)?cestino)'
    r'|(?P<finder>apri\s+finder|mostra\s+finder)'
    r'|(?P<desktop_show>mostra\s+(?:le\s+icone\s+del\s+)?desktop|mostra\s+file\s+desktop)'
    r'|(?P<desktop_hide>nascondi\s+(?:le\s+icone\s+del\s+)?desktop|nascondi\s+file\s+desktop)'
    r'|(?P<wallpaper>(?:cambia|imposta|metti)\s+(?:lo\s+)?sfondo\s+(?:con\s+|a\s+)?(?P<wp_path>[^\s,]+))'
    r')',
    re.I,
)


def _osascript(script: str) -> tuple[int, str]:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode, r.stderr.strip()


class DesktopControlSkill(Skill):
    name        = "desktop_control"
    description = "Controlla Dock, Finder, sfondo desktop e cestino macOS."

    def match(self, text: str) -> dict | None:
        m = _RE.search(text)
        if not m:
            return None
        groups = {k: v for k, v in m.groupdict().items() if v and k != "wp_path"}
        return {"groups": groups, "wp_path": m.group("wp_path")}

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._execute, params["groups"], params.get("wp_path")
        )

    def _execute(self, groups: dict, wp_path: str | None) -> str:
        if "dock_hide" in groups:
            _osascript('tell application "System Events" to tell dock preferences to set autohide to true')
            return "[DESKTOP] Dock impostato in auto-hide."

        if "dock_show" in groups:
            _osascript('tell application "System Events" to tell dock preferences to set autohide to false')
            return "[DESKTOP] Dock sempre visibile."

        if "trash_empty" in groups:
            code, err = _osascript('tell application "Finder" to empty trash')
            return "[DESKTOP] Cestino svuotato." if code == 0 else f"[DESKTOP] {err or 'Errore svuotamento cestino.'}"

        if "finder" in groups:
            subprocess.run(["open", "-a", "Finder"], capture_output=True)
            return "[DESKTOP] Finder aperto."

        if "desktop_show" in groups:
            _osascript('tell application "Finder" to set desktop picture to POSIX file "/System/Library/Desktop Pictures/Solid Colors/Black.png"')
            subprocess.run(["defaults", "write", "com.apple.finder", "CreateDesktop", "true"], capture_output=True)
            subprocess.run(["killall", "Finder"], capture_output=True)
            return "[DESKTOP] Icone desktop visibili (Finder riavviato)."

        if "desktop_hide" in groups:
            subprocess.run(["defaults", "write", "com.apple.finder", "CreateDesktop", "false"], capture_output=True)
            subprocess.run(["killall", "Finder"], capture_output=True)
            return "[DESKTOP] Icone desktop nascoste (Finder riavviato)."

        if "wallpaper" in groups and wp_path:
            import os
            path = os.path.expanduser(wp_path)
            script = f'''
tell application "System Events"
    tell every desktop
        set picture to POSIX file "{path}"
    end tell
end tell'''
            code, err = _osascript(script)
            return f"[DESKTOP] Sfondo cambiato: {path}" if code == 0 else f"[DESKTOP] Errore sfondo: {err}"

        return "[DESKTOP] Azione non riconosciuta."
